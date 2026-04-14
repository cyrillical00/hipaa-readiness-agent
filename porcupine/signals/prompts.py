"""
Chain-of-thought probability elicitation prompts for LLM forecasters.

Design rationale:
- LLMs are not calibrated forecasters out of the box. Without scaffolding they
  anchor on salient numbers (e.g. the market price we provide) or return round
  numbers like 0.5.
- CoT forces the model to reason before committing to a number.
- Calibration anchors (base rates, reference classes) reduce overconfidence.
- Strict JSON response format makes parsing deterministic.
"""

from __future__ import annotations


SYSTEM_PROMPT = """\
You are a calibrated probabilistic forecaster. Your job is to estimate the \
probability that a YES outcome occurs in a prediction market. You are \
epistemically honest, avoid anchoring on the current market price, and express \
genuine uncertainty through your confidence rating.
"""


def build_user_prompt(question: str, implied_prob: float, end_date: str | None) -> str:
    """
    Build the CoT elicitation prompt for a single market.

    Args:
        question:     The market question (e.g. "Will X happen by Y?")
        implied_prob: Current Polymarket YES token price (0.0–1.0)
        end_date:     Resolution date string (ISO or human-readable)

    Returns:
        A multi-step reasoning prompt that forces structured JSON output.
    """
    end_str = end_date if end_date else "unspecified"
    implied_pct = f"{implied_prob * 100:.1f}%"

    return f"""\
You are evaluating the following prediction market:

  Question:       {question}
  Resolution by: {end_str}
  Market price:  {implied_pct} (this is the crowd's implied probability — use it as one data point, not an anchor)

Work through the following steps before giving your estimate:

1. **Arguments FOR YES** — List the 2–3 strongest reasons this resolves YES.
2. **Arguments FOR NO** — List the 2–3 strongest reasons this resolves NO.
3. **Base rates / reference class** — Is there a relevant historical base rate \
(e.g., how often does this type of event occur)? Cite it if known.
4. **Inside vs outside view** — Does the specific context push your estimate \
above or below the base rate? Explain briefly.
5. **Probability estimate** — State your final probability as a decimal between \
0.00 and 1.00. Do NOT simply repeat the market price.

After your reasoning, output ONLY the following JSON on a new line — no other text:

{{"estimate": <float 0.00-1.00>, "rationale": "<one-sentence summary>", "confidence": "<low|medium|high>"}}
"""


def build_retry_prompt() -> str:
    """
    Fallback prompt used when the model returned malformed JSON.
    Strips reasoning steps and demands the JSON directly.
    """
    return """\
Your previous response could not be parsed as valid JSON. Please respond with ONLY \
the following JSON object and nothing else:

{"estimate": <float between 0.00 and 1.00>, "rationale": "<one sentence>", "confidence": "<low|medium|high>"}
"""
