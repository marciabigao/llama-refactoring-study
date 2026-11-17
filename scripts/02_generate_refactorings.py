"""Tarefas 1.2–1.4 — Gera as refatorações com um LLM aberto via API compatível com OpenAI
(padrão do projeto: Groq + qwen/qwen3.8-27b; também funciona com SambaNova e Fireworks).

Protocolo do artigo: temperature=1.0, top_p=1.0, max_tokens=4000, prompt de sistema da Seção 3.2.
- Ordem: ciclo por ciclo (ciclo 0 em todas as classes, depois ciclo 1...). Se parar, você já tem ciclos completos.
- Retomável: gerações já salvas em results/<modelo>/raw/ são puladas.
- --plan --days N : estima quantos ciclos cabem em N dias dado o limite diário de tokens (não chama a API).
- --auto-resume   : quando a cota DIÁRIA acaba, dorme até o reset (o servidor informa) e continua sozinho.
- LLM_MODEL=mock  : respostas falsas para testar o pipeline sem API.

Exemplos:
    python scripts/02_generate_refactorings.py --plan --days 3
    python scripts/02_generate_refactorings.py --tasks 3 --runs 2            # teste rápido
    python scripts/02_generate_refactorings.py --auto-resume                 # experimento completo, sem supervisão
"""
import argparse
import json
import os
import re
import time
import zlib
from collections import deque
from datetime import datetime, timezone

from tqdm import tqdm

from _common import config, load_tasks, task_sort_key
from src.prompts import build_system_prompt, build_user_prompt


class FatalError(Exception):
    """Erro que não adianta tentar de novo (chave, modelo, saldo, parâmetro inválido)."""


class TooLarge(Exception):
    """Esta requisição nunca cabe no limite por minuto (Requested > Limit) ou foi barrada muitas vezes seguidas."""


class DailyLimit(Exception):
    """Cota diária (tokens/requisições) esgotada. `wait` = segundos até o reset, se o servidor informou."""

    def __init__(self, msg, wait=None):
        super().__init__(msg)
        self.wait = wait


def parse_wait(msg: str, default=None):
    """Lê 'Please try again in 17m3.5s' / '2h30m' / '250ms' (formato das mensagens 429 da Groq)."""
    m = re.search(r"try again in\s*([\d.]+)\s*ms\b", msg)
    if m:
        return float(m.group(1)) / 1000
    m = re.search(r"try again in\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?!s))?\s*(?:([\d.]+)\s*s)?", msg)
    if not m or not any(m.groups()):
        return default
    h, mi, sec = (float(x) if x else 0.0 for x in m.groups())
    return h * 3600 + mi * 60 + sec


def header_seconds(headers, name):
    try:
        return float(headers.get(name))
    except (TypeError, ValueError):
        return None


def mock_response(task: dict, it: int) -> dict:
    """Resposta falsa p/ testar o pipeline. ~1/7 das gerações recebem um bug sintético."""
    code = task["solution_code"]
    if zlib.crc32(f"{task['task_id']}-{it}".encode()) % 7 == 0:
        code = code.replace(" + ", " - ", 1) if " + " in code else code.replace(" == ", " != ", 1)
    fence = "`" * 3
    text = f"{fence}python\n{code}\n{fence}\n\n{fence}text\nExtract Method, Inline Method, Rename Variable\n{fence}"
    return {"text": text, "finish_reason": "stop", "usage": {}}


def call_llm(client, system, user):
    import openai
    attempt = 0
    kwargs = dict(model=config.MODEL,
                  messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                  temperature=config.TEMPERATURE, top_p=config.TOP_P, max_tokens=config.MAX_TOKENS, n=1)
    if config.REASONING_EFFORT:
        kwargs["extra_body"] = {"reasoning_effort": config.REASONING_EFFORT}
    while True:
        try:
            raw = client.chat.completions.with_raw_response.create(**kwargs)
            r = raw.parse()
            ch = r.choices[0]
            u = r.usage
            h = raw.headers
            usage = {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens} if u else {}
            det = getattr(u, "completion_tokens_details", None) if u else None
            if getattr(det, "reasoning_tokens", None) is not None:
                usage["reasoning_tokens"] = det.reasoning_tokens
            reasoning = getattr(ch.message, "reasoning", None)
            return {"text": ch.message.content or "", "finish_reason": ch.finish_reason, "usage": usage,
                    "reasoning_chars": len(reasoning) if reasoning else 0,
                    "rate_limit": {"remaining_day": h.get("x-ratelimit-remaining-requests-day"),
                                   "reset_day": h.get("x-ratelimit-reset-requests-day")}}
        except openai.RateLimitError as e:
            msg = str(e)
            hdr = getattr(getattr(e, "response", None), "headers", {}) or {}
            per_day = hdr.get("x-ratelimit-remaining-requests-day") == "0" or \
                re.search(r"per day|\bTPD\b|\bRPD\b|daily", msg, re.I)
            per_min = re.search(r"per minute|\b[OI]?TPM\b|\bRPM\b", msg)
            if per_day and not per_min:
                wait = parse_wait(msg) or header_seconds(hdr, "x-ratelimit-reset-requests-day") or \
                    header_seconds(hdr, "retry-after")
                raise DailyLimit(f"cota DIÁRIA esgotada: {msg}", wait)
            lim = re.search(r"Limit\s+(\d+),\s*Used\s+(\d+),\s*Requested\s+(\d+)", msg)
            if per_min and lim and int(lim.group(3)) > int(lim.group(1)):
                raise TooLarge(f"pedido maior que o limite por minuto inteiro: {msg}")
            if re.search(r"insufficient (funds|balance|credit)|exceeded your (current )?quota|payment required", msg, re.I):
                raise FatalError(f"saldo/cota esgotado: {msg}")
            # qualquer outro 429 (inclui limite por minuto de tokens de entrada/saída): esperar e repetir
            attempt += 1
            if attempt > 12:
                raise TooLarge(f"barrado {attempt} vezes seguidas pelo limite por minuto: {msg}")
            wait = parse_wait(msg) or header_seconds(hdr, "retry-after") or 2 ** min(attempt, 6)
            wait = min(wait + 1.0, 120.0)
            tqdm.write(f"  [429 por minuto] aguardando {wait:.0f}s (tentativa {attempt})")
            time.sleep(wait)
        except openai.NotFoundError as e:
            raise FatalError(f"modelo não encontrado ({config.MODEL}). Confira LLM_MODEL no .env. Detalhe: {e}")
        except (openai.AuthenticationError, openai.PermissionDeniedError) as e:
            raise FatalError(f"chave inválida ou sem permissão: {e}")
        except (openai.APIConnectionError, openai.APITimeoutError, openai.InternalServerError) as e:
            attempt += 1
            if attempt > 6:
                raise
            wait = min(2 ** attempt, 60)
            tqdm.write(f"  [rede/servidor] {type(e).__name__}; tentativa {attempt}, aguardando {wait}s")
            time.sleep(wait)
        except openai.BadRequestError as e:
            raise FatalError(f"requisição recusada (400): {e}. Se citar 'reasoning_effort', "
                             f"remova/ajuste LLM_REASONING_EFFORT no .env.")
        except openai.APIStatusError as e:
            if e.status_code in (402, 412):
                raise FatalError(f"conta sem saldo/suspensa (HTTP {e.status_code}): {e}")
            raise


class Pacer:
    """Janela deslizante de 60 s p/ respeitar TPM (tokens totais) e OTPM (tokens de saída) sem tomar 429."""

    def __init__(self, tpm, otpm):
        self.tpm, self.otpm, self.win, self.recent_out = tpm, otpm, deque(), deque(maxlen=5)

    def wait(self, est_in, est_out):
        if not (self.tpm or self.otpm):
            return
        est_out = max(est_out, sum(self.recent_out) / len(self.recent_out) if self.recent_out else 0)
        while True:
            now = time.time()
            while self.win and now - self.win[0][0] > 60:
                self.win.popleft()
            tot, out = sum(w[1] for w in self.win), sum(w[2] for w in self.win)
            fits = (not self.tpm or tot + est_in + est_out <= self.tpm * 0.92) and \
                   (not self.otpm or out + est_out <= self.otpm * 0.92)
            if fits or not self.win:   # janela vazia: manda mesmo que estimativa > limite (o servidor decide)
                return
            time.sleep(max(0.5, self.win[0][0] + 60 - now + 0.2))

    def record(self, total, out):
        self.win.append((time.time(), total, out))
        self.recent_out.append(out)


def plan(tasks, ids, n_runs, days):
    """Estima quantos ciclos cabem em `days` dias com a cota diária configurada."""
    measured = []
    for f in config.RAW_DIR.glob("*.json"):
        u = json.loads(f.read_text(encoding="utf-8")).get("usage") or {}
        if u.get("prompt_tokens"):
            measured.append(u["prompt_tokens"] + u.get("completion_tokens", 0))
    if len(measured) >= 5:
        tpg, src = sum(measured) / len(measured), f"MEDIDO em {len(measured)} gerações reais"
    else:
        sys_t = len(build_system_prompt()) / 3.3
        code_t = sum(len(tasks[t]["solution_code"]) for t in ids) / len(ids) / 3.3
        tpg, src = sys_t + code_t + (1.3 * code_t + 80), "ESTIMADO (chars/3,3; saída≈1,3× o código) — rode 5+ gerações p/ medir"
    total = len(ids) * n_runs
    print(f"Modelo: {config.MODEL} | tokens por geração ≈ {tpg:,.0f} ({src})")
    print(f"Pedido: {len(ids)} classes × {n_runs} ciclos = {total} gerações ≈ {total * tpg / 1e6:.2f} M tokens")
    if config.OTPM_LIMIT:
        out_total = total * (tpg - (len(build_system_prompt()) / 3.3 + sum(len(tasks[t]["solution_code"]) for t in ids) / len(ids) / 3.3))
        print(f"Limite por minuto: OTPM={config.OTPM_LIMIT} => saída total ≈ {out_total / 1e3:.0f}k tokens "
              f"=> ritmo mínimo ≈ {out_total / config.OTPM_LIMIT / 60:.1f} h de relógio (não é o gargalo se couber nos dias)")
    q_tok, q_req = config.DAILY_TOKEN_QUOTA, config.DAILY_REQUEST_QUOTA
    if not q_tok and not q_req:
        print("Sem cota diária configurada (plano pago/ilimitado): o limite passa a ser só a taxa por minuto.")
        return
    per_day = min(int(q_tok * 0.95 / tpg) if q_tok else 10 ** 9, q_req or 10 ** 9)
    need = total / per_day
    print(f"Cota diária: {q_tok:,} tokens / {q_req or '∞'} req (usando 95% de margem) => ~{per_day} gerações/dia")
    print(f"Tempo para {n_runs} ciclos: ~{need:.1f} dia(s)")
    if days:
        cap = per_day * days
        fit_max = int(cap // len(ids))
        fit = int(cap * 0.85 // len(ids))  # 15% de folga p/ respostas mais longas que o previsto, falhas e retentativas
        verdict = "CABE" if total <= cap * 0.85 else ("APERTADO (sem folga)" if total <= cap else "NÃO CABE")
        print(f"Em {days:g} dia(s): {verdict}. Capacidade ≈ {cap} gerações.")
        print(f"  -> N_RUNS RECOMENDADO (com 15% de folga): {fit}  | máximo teórico: {fit_max}")
        if fit < 1:
            print("  -> nem 1 ciclo completo cabe; reduza o nº de classes ou use plano pago.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=int, default=None, help="usar só as N primeiras classes (teste)")
    ap.add_argument("--runs", type=int, default=None, help="número de ciclos (padrão: N_RUNS do .env)")
    ap.add_argument("--plan", action="store_true", help="só estima tempo/custo em tokens e sai")
    ap.add_argument("--days", type=float, default=None, help="(com --plan) prazo em dias")
    ap.add_argument("--auto-resume", action="store_true",
                    help="ao esgotar a cota diária, dorme até o reset e continua sozinho")
    args = ap.parse_args()

    config.ensure_dirs()
    tasks = load_tasks()
    ids = sorted(tasks, key=task_sort_key)[: args.tasks]
    n_runs = args.runs or config.N_RUNS
    if args.plan:
        plan(tasks, ids, n_runs, args.days)
        return
    system = build_system_prompt()

    (config.RESULTS_DIR / "experiment_config.json").write_text(json.dumps({
        "provider": config.PROVIDER, "model": config.MODEL, "temperature": config.TEMPERATURE,
        "top_p": config.TOP_P, "max_tokens": config.MAX_TOKENS, "reasoning_effort": config.REASONING_EFFORT or None,
        "n_runs": n_runs, "n_tasks": len(ids), "system_prompt": system,
        "user_prompt": "<solution_code da classe do ClassEval>",
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    client = None
    if config.MODEL != "mock":
        if not config.API_KEY:
            raise SystemExit(f"[erro] defina {config.PROVIDERS[config.PROVIDER]['key_env']} no .env")
        from openai import OpenAI
        client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL, max_retries=0, timeout=180)

    margin = float(os.getenv("RESUME_MARGIN_S", "30"))
    pacer = Pacer(config.TPM_LIMIT, config.OTPM_LIMIT)
    skipped = []
    jobs = [(it, tid) for it in range(n_runs) for tid in ids
            if not (config.RAW_DIR / f"{tid}__iter{it}.json").exists()]
    print(f"Modelo: {config.MODEL} | pendentes: {len(jobs)} de {len(ids) * n_runs} | auto-resume: {args.auto_resume}")
    last = 0.0
    try:
        for it, tid in tqdm(jobs, unit="ger"):
            while True:
                try:
                    if client is None:
                        resp = mock_response(tasks[tid], it)
                    else:
                        dt = time.time() - last
                        if dt < config.REQUEST_INTERVAL_S:
                            time.sleep(config.REQUEST_INTERVAL_S - dt)
                        user = build_user_prompt(tasks[tid])
                        pacer.wait((len(system) + len(user)) / 3.3, 1.6 * len(user) / 3.3 + 60)
                        last = time.time()
                        resp = call_llm(client, system, user)
                        u = resp.get("usage") or {}
                        pacer.record(u.get("prompt_tokens", 0) + u.get("completion_tokens", 0), u.get("completion_tokens", 0))
                    break
                except TooLarge as e:
                    skipped.append(f"{tid}#{it}")
                    tqdm.write(f"  [PULADA] {tid} ciclo {it}: {str(e)[:200]}")
                    resp = {"text": "", "finish_reason": "rate_limit_too_large", "usage": {}, "error": str(e)[:500]}
                    break
                except DailyLimit as e:
                    if not args.auto_resume:
                        raise FatalError(f"{e}\nRode de novo depois (ou use --auto-resume para continuar sozinho).")
                    wait = min((e.wait or 3600) + margin, 26 * 3600)
                    tqdm.write(f"  [COTA DIÁRIA] dormindo {wait / 60:.0f} min até o reset "
                               f"(retoma às {datetime.fromtimestamp(time.time() + wait):%d/%m %H:%M})")
                    time.sleep(wait)
            rec = {"task_id": tid, "iteration": it, "model": config.MODEL,
                   "timestamp": datetime.now(timezone.utc).isoformat(), **resp}
            tmp = config.RAW_DIR / f".{tid}__iter{it}.tmp"
            tmp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            tmp.replace(config.RAW_DIR / f"{tid}__iter{it}.json")  # escrita atômica
            rl = resp.get("rate_limit", {})
            if str(rl.get("remaining_day")) == "0":  # SambaNova informa a cota restante nos cabeçalhos
                wait = float(rl.get("reset_day") or 3600) + margin
                if not args.auto_resume:
                    print(f"\n[COTA DIÁRIA CONSUMIDA] última requisição de hoje. Progresso salvo; rode amanhã.")
                    break
                tqdm.write(f"  [COTA DIÁRIA] dormindo {wait / 60:.0f} min até o reset")
                time.sleep(wait)
    except FatalError as e:
        print(f"\n[PARADO] {e}\nO progresso está salvo; corrija e rode o script de novo para continuar.")
    except KeyboardInterrupt:
        print("\nInterrompido. Progresso salvo; rode novamente para continuar.")
    if skipped:
        print(f"\n[ATENÇÃO] {len(skipped)} geração(ões) PULADA(S) por exceder o limite por minuto do seu plano: {skipped[:10]}"
              f"{' ...' if len(skipped) > 10 else ''}\n  Elas contam como falha no RQ1 (status 'skipped_rate_limit'); "
              f"use `05_rq1_metrics.py --exclude-skipped` p/ reportar sem elas e declare isso. "
              f"Para gerá-las, apague os .json correspondentes em raw/ após subir de plano e rode de novo.")
    done = len(list(config.RAW_DIR.glob("*.json")))
    print(f"Gerações salvas: {done}/{len(ids) * n_runs}")


if __name__ == "__main__":
    main()
