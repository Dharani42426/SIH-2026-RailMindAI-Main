# ═══════════════════════════════════════════════════════════════
# RailMind AI — NLP Command Processor
# AI Component #8: Natural Language Interface for Controllers
# Parses Hindi/English commands into API actions
#
# Architecture:
#   NLP_PROVIDER="ollama"  → Qwen3-235B via Ollama → structured JSON → merge with regex entities
#   NLP_PROVIDER="pattern" → existing regex parser (default, always available as fallback)
# ═══════════════════════════════════════════════════════════════

import json
import logging
import re
from datetime import date, timedelta
from typing import Optional

import requests


class NLPProcessor:
    """
    Natural language command parser for railway controllers.

    WHAT IT DOES:
    - Parses Hindi/English commands from Section Controllers
    - Extracts entities (section, task type, date range)
    - Maps to API actions
    - Generates natural language responses

    APPROACH:
    - Primary: Ollama / Qwen3-235B-A22B for intent detection (when NLP_PROVIDER="ollama")
    - Fallback: Pattern matching + keyword extraction (always available)

    The system never fails due to Ollama being unavailable — regex fallback
    is always engaged automatically on any LLM error.

    EXAMPLE COMMANDS:
    - "Show available blocks for track tamping on Kalyan-Kasara next week"
    - "Kalyan section mein rail fracture ka kya status hai?"
    - "Schedule emergency block for OHE repair near KM 65"
    - "What are the top 5 critical tasks?"
    """

    # ─── Intent Patterns ───
    INTENT_PATTERNS = {
        "QUERY_BLOCKS": [
            r"show.*block", r"available.*block", r"block.*available",
            r"kab.*block", r"block.*kab", r"find.*window",
            r"get.*block", r"list.*block",
        ],
        "QUERY_TASKS": [
            r"show.*task", r"pending.*task", r"critical.*task",
            r"top.*task", r"overdue.*task", r"defect.*status",
            r"kya.*status", r"status.*kya", r"list.*defect",
        ],
        "SCHEDULE": [
            r"schedule.*block", r"create.*block", r"plan.*block",
            r"emergency.*block", r"request.*block",
            r"schedule.*maintenance", r"book.*block",
        ],
        "STATUS": [
            r"status.*section", r"health.*section", r"condition",
            r"section.*status", r"track.*condition", r"asset.*health",
            r"section.*kaisi", r"kaisa.*hai",
        ],
        "OPTIMIZE": [
            r"optimize", r"generate.*plan", r"auto.*schedule",
            r"ai.*plan", r"best.*schedule", r"optimal",
        ],
        "PREDICT": [
            r"predict", r"forecast", r"when.*fail", r"remaining.*life",
            r"kab.*fail", r"risk.*assessment", r"future.*health",
        ],
        "HELP": [
            r"help", r"madad", r"kaise", r"how.*to", r"what.*can",
            r"commands", r"options",
        ],
    }

    # ─── Section Code Mapping (aliases) ───
    # IMPORTANT: Compound names ("kalyan-kasara") must match before single words ("kalyan")
    # We sort by length descending at lookup time to guarantee this.
    SECTION_ALIASES = {
        # Compound section references (MUST match first)
        "kalyan-kasara": "KYN-KAS", "kalyan kasara": "KYN-KAS",
        "kalyan to kasara": "KYN-KAS", "kyn-kas": "KYN-KAS",
        "kyn - kas": "KYN-KAS", "kyn–kas": "KYN-KAS", "kyn to kas": "KYN-KAS",
        "kasara ghat": "KYN-KAS", "ghat section": "KYN-KAS",
        "csmt-dadar": "CSMT-DR", "csmt to dadar": "CSMT-DR", "csmt-dr": "CSMT-DR",
        "dadar-thane": "DR-TNA", "dadar to thane": "DR-TNA", "dr-tna": "DR-TNA",
        "thane-kalyan": "TNA-KYN", "thane to kalyan": "TNA-KYN", "tna-kyn": "TNA-KYN",
        "kalyan-karjat": "KYN-KJT", "kalyan to karjat": "KYN-KJT", "kyn-kjt": "KYN-KJT",
        "karjat-lonavala": "KJT-LNL", "karjat to lonavala": "KJT-LNL", "kjt-lnl": "KJT-LNL",
        "lonavala-pune": "LNL-PUNE", "lonavala to pune": "LNL-PUNE", "lnl-pune": "LNL-PUNE",
        "csmt-panvel": "CSMT-PL", "csmt to panvel": "CSMT-PL", "csmt-pl": "CSMT-PL",
        "igatpuri-manmad": "IGP-MAS", "igp-mas": "IGP-MAS",
        "manmad-bhusawal": "MAS-BSL", "mas-bsl": "MAS-BSL",
        # Single station aliases (checked AFTER compounds)
        "csmt": "CSMT-DR", "mumbai": "CSMT-DR", "dadar": "CSMT-DR",
        "thane": "DR-TNA", "ghatkopar": "DR-TNA", "kurla": "DR-TNA",
        "kalyan": "TNA-KYN", "dombivli": "TNA-KYN", "diva": "TNA-KYN",
        "kasara": "KYN-KAS", "igatpuri": "KYN-KAS", "thakurwadi": "KYN-KAS",
        "karjat": "KYN-KJT", "badlapur": "KYN-KJT", "neral": "KYN-KJT",
        "lonavala": "KJT-LNL", "khandala": "KJT-LNL",
        "pune": "LNL-PUNE", "talegaon": "LNL-PUNE",
        "panvel": "CSMT-PL", "vashi": "CSMT-PL", "harbour": "CSMT-PL",
        "manmad": "IGP-MAS", "nasik": "IGP-MAS", "nashik": "IGP-MAS",
        "bhusawal": "MAS-BSL", "jalgaon": "MAS-BSL",
    }

    # ─── Department Keywords ───
    DEPARTMENT_KEYWORDS = {
        "ENGG": ["track", "rail", "sleeper", "ballast", "bridge", "tamping",
                 "fracture", "gauge", "alignment", "p&c", "engineering",
                 "patri", "pul", "track"],
        "SNT": ["signal", "point machine", "track circuit", "relay",
                "interlocking", "axle counter", "telecom", "fiber",
                "signal", "snt"],
        "TRD": ["ohe", "overhead", "wire", "mast", "insulator", "power",
                "traction", "pantograph", "catenary", "bijli", "trd"],
    }

    # ─── Time Keywords ───
    TIME_KEYWORDS = {
        "today": 0,
        "tomorrow": 1, "kal": 1,
        "next week": 7, "agle hafte": 7,
        "next month": 30, "agle mahine": 30,
        "this week": 0,
        "urgent": 0, "emergency": 0,
    }

    def __init__(self):
        """
        Initialize NLPProcessor with configuration from settings.

        Reads NLP_PROVIDER, NVIDIA, and Ollama settings from the app config.
        Creates the LLMRouter for primary/secondary failover.
        Safe to call with no arguments.
        """
        try:
            from config import get_settings
            settings = get_settings()
            self._nlp_provider = settings.NLP_PROVIDER.lower()
            self._ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
            self._ollama_model = settings.OLLAMA_MODEL
            self._ollama_timeout = settings.OLLAMA_TIMEOUT_SECONDS
        except Exception:
            self._nlp_provider = "pattern"
            self._ollama_base_url = "http://10.10.50.250:11434"
            self._ollama_model = "qwen3:235b"
            self._ollama_timeout = 120

        self._logger = logging.getLogger("railmind.nlp")

        # Initialize LLM Router for nvidia/ollama providers
        self._llm_router = None
        if self._nlp_provider in ("nvidia", "ollama"):
            try:
                from services.llm_providers import create_llm_router_from_settings
                self._llm_router = create_llm_router_from_settings()
            except Exception as e:
                self._logger.warning("LLM Router init failed, will use regex-only: %s", e)

        # Pre-compute valid sets for LLM output validation
        self._valid_intents = set(self.INTENT_PATTERNS.keys())
        self._valid_sections = set(self.SECTION_ALIASES.values())
        self._valid_departments = set(self.DEPARTMENT_KEYWORDS.keys())
        self._valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        self._valid_timeframes = set(self.TIME_KEYWORDS.keys())

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def process_command(self, command: str) -> dict:
        """
        Process a natural language command and return structured result.

        When NLP_PROVIDER is "nvidia":
          1. Call Nemotron via NVIDIA API (primary), Qwen via Ollama (fallback)
          2. Run regex extraction in parallel
          3. Merge results (regex wins for deterministic matches)
          4. Falls back to regex-only on any LLM failure

        When NLP_PROVIDER is "ollama":
          Uses Qwen via LLMRouter (same flow, Ollama as primary)

        When NLP_PROVIDER is "pattern" (default):
          Uses regex-only detection (original behavior)
        """
        command_lower = command.lower().strip()
        ai_engine = None

        if self._nlp_provider in ("nvidia", "ollama") and self._llm_router:
            try:
                intent, llm_entities, ai_engine = self._detect_intent_with_llm_router(command)
                regex_entities = self._extract_entities(command_lower)
                entities = self._merge_entities(regex_entities, llm_entities)
            except Exception as e:
                self._logger.warning(
                    "LLM NLP failed, falling back to regex: %s", e
                )
                intent = self._detect_intent(command_lower)
                entities = self._extract_entities(command_lower)
                ai_engine = "Deterministic Fallback"
        else:
            intent = self._detect_intent(command_lower)
            entities = self._extract_entities(command_lower)
            ai_engine = "Deterministic Fallback"

        api_action = self._map_to_api(intent, entities)
        response_text = self._generate_response(intent, entities)

        result = {
            "original_command": command,
            "intent": intent,
            "entities": entities,
            "api_action": api_action,
            "response_text": response_text,
        }
        if ai_engine:
            result["ai_engine"] = ai_engine
        return result

    # ─────────────────────────────────────────────────────────────
    # OLLAMA / QWEN3 INTEGRATION
    # ─────────────────────────────────────────────────────────────

    def _detect_intent_with_llm_router(self, command: str) -> tuple:
        """
        Detect intent and extract entities using the LLM Router.

        Routes through NVIDIA Nemotron (primary) -> Qwen/Ollama (secondary).
        Returns: (intent, entities, ai_engine_string)
        Raises Exception on failure (caller falls back to regex).
        """
        system_prompt = self._build_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command},
        ]

        response = self._llm_router.generate(messages, temperature=0.1)

        try:
            raw_content = response.content
            if not raw_content:
                raise ValueError("Empty response content from LLM")

            parsed = self._parse_llm_json(raw_content)
            intent = self._validate_intent(parsed)
            entities = self._validate_llm_entities(parsed)
        except (ValueError, TypeError) as e:
            # If primary produced malformed output, try secondary
            if self._llm_router.secondary and getattr(response, "provider", None) == 'nvidia':
                self._logger.warning("Primary returned malformed output, falling back to Qwen: %s", e)
                response = self._llm_router.secondary.generate(messages, temperature=0.1)
                response.fallback_used = True
                raw_content = response.content
                if not raw_content:
                    raise ValueError("Empty response content from Qwen")
                parsed = self._parse_llm_json(raw_content)
                intent = self._validate_intent(parsed)
                entities = self._validate_llm_entities(parsed)
            else:
                raise

        # Build ai_engine display string
        model_display = response.model
        if response.provider == 'nvidia':
            model_display = 'Nemotron'
        elif response.provider == 'ollama':
            model_display = 'Qwen3-235B'

        ai_engine = model_display
        if response.fallback_used:
            ai_engine = 'Qwen3-235B'

        self._logger.info(
            "LLM NLP result: provider=%s model=%s fallback=%s latency=%.0fms",
            response.provider, response.model, response.fallback_used, response.latency_ms
        )

        return intent, entities, ai_engine

    def _build_system_prompt(self) -> str:
        """
        Build the provider-independent system prompt that grounds the LLM in RailMind's domain.

        Includes all valid section codes, department keywords, intent semantics,
        and Hindi/Hinglish understanding instructions.
        """
        # Build section code reference from existing SECTION_ALIASES
        section_codes = sorted(self._valid_sections)
        section_aliases_examples = []
        for alias, code in sorted(self.SECTION_ALIASES.items(), key=lambda x: x[1]):
            section_aliases_examples.append(f'  "{alias}" → {code}')
        section_aliases_str = "\n".join(section_aliases_examples)

        return f"""You are RailMind AI's NLP command parser for Indian Railways block maintenance planning.

Your ONLY job is to parse a user command into a structured JSON object. 
Do NOT explain anything. Do NOT output chain-of-thought or reasoning. 
Do NOT add any text outside the JSON object.

## Valid Intents (pick EXACTLY one):
- QUERY_BLOCKS: user wants to see available block windows, free blocks, suitable blocks, "kab block milega", block availability
- QUERY_TASKS: user wants to see pending/overdue/critical tasks, defects, maintenance tasks, "kya pending hai"
- SCHEDULE: user wants to schedule/create/book/request an actual maintenance block
- STATUS: user wants health/status/condition of a section or assets, "kaisa hai"
- OPTIMIZE: user wants AI optimization, generate best plan, automatic planning
- PREDICT: user wants failure prediction, forecast, remaining life, future risk
- HELP: user asks for help, commands list, how to use

IMPORTANT: A user asking about "suitable block" or "block availability" for some work is QUERY_BLOCKS, NOT SCHEDULE.
Example: "OHE ka kaam hai, suitable block batao" → QUERY_BLOCKS (they want to SEE blocks, not create one)

## Valid Section Codes (use ONLY these):
{", ".join(section_codes)}

Section alias mapping (user may use any of these names):
{section_aliases_str}

If the user mentions a location not in this list, set section to null.

## Valid Departments:
- ENGG: track, rail, sleeper, ballast, bridge, tamping, fracture, gauge, alignment, P&C, engineering, patri, pul
- SNT: signal, point machine, track circuit, relay, interlocking, axle counter, telecom, fiber
- TRD: OHE, overhead wire, mast, insulator, power, traction, pantograph, catenary, bijli

"OHE" → TRD (NOT ENGG)
"track tamping" → ENGG
"signal relay" → SNT

## Valid Severities:
CRITICAL, HIGH, MEDIUM, LOW

## Valid Timeframes:
today, tomorrow, next week, next month, this week

Hindi equivalents: "kal" = tomorrow, "agle hafte" = next week, "agle mahine" = next month

## Language
You understand Hindi, Hinglish (Hindi mixed with English), and English equally well.
Examples:
- "Kasara section mein kya pending hai?" → QUERY_TASKS, section=KYN-KAS
- "OHE ka kaam kab kar sakte hain?" → QUERY_BLOCKS, department=TRD
- "signal ka status batao" → STATUS, department=SNT
- "agle hafte ke liye blocks dikhao" → QUERY_BLOCKS, timeframe=next week
- "critical tasks dikhao" → QUERY_TASKS, severity=CRITICAL

## Output Format
Return ONLY this strict JSON format (no markdown, no explanation, no extra text):
{{
  "intent": "...",
  "action": "...",
  "section": "... or null",
  "asset": "... or null",
  "department": "... or null",
  "parameters": {{
     "severity": "... or null",
     "timeframe": "... or null",
     "km_location": <number or null>,
     "limit": <integer or null>
  }}
}}"""

    def _detect_intent_with_ollama(self, command: str) -> tuple:
        """
        Detect intent and extract entities using Ollama + Qwen3-235B.

        Calls POST {OLLAMA_BASE_URL}/api/chat with stream=false.

        Returns:
            (intent: str, entities: dict)

        Raises:
            Exception on any failure (timeout, invalid JSON, bad values, etc.)
            — caller catches this and falls back to regex.
        """
        system_prompt = self._build_system_prompt()

        payload = {
            "model": self._ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
            # Disable thinking/reasoning for short structured output
            "think": False,
        }

        url = f"{self._ollama_base_url}/api/chat"

        response = requests.post(
            url,
            json=payload,
            timeout=self._ollama_timeout,
        )
        response.raise_for_status()

        response_data = response.json()
        raw_content = response_data.get("message", {}).get("content", "")

        if not raw_content:
            raise ValueError("Empty response content from Ollama")

        # Parse the JSON — strip markdown code fences if present
        parsed = self._parse_llm_json(raw_content)

        # Validate and extract
        intent = self._validate_intent(parsed)
        entities = self._validate_llm_entities(parsed)

        return intent, entities

    def _parse_llm_json(self, raw: str) -> dict:
        """
        Parse JSON from LLM response, handling various wrapper formats.

        Qwen3 models may include <think>...</think> reasoning blocks even
        when think=false is set. This method strips:
        1. <think>...</think> reasoning tags (with or without opening <think>)
        2. ```json ... ``` markdown code fences
        3. Any other text before/after the JSON object
        """
        text = raw.strip()

        # Strip <think>...</think> blocks
        # Qwen3 sometimes omits the opening <think> tag but always has </think>
        if "</think>" in text:
            think_end = text.index("</think>")
            text = text[think_end + len("</think>"):].strip()

        # Strip markdown code fences
        if text.startswith("```"):
            # Remove opening fence (possibly with language tag)
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
            # Remove closing fence
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3].rstrip()

        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: find the first JSON object in the text using braces
        # This handles cases where there's extra text around the JSON
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_str = text[brace_start:brace_end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Invalid JSON from Ollama: could not extract JSON from response")

    def _validate_intent(self, parsed: dict) -> str:
        """Validate and return the intent from parsed LLM output."""
        intent = parsed.get("intent")
        if not intent or intent not in self._valid_intents:
            raise ValueError(
                f"Invalid intent from Ollama: '{intent}'. "
                f"Valid: {self._valid_intents}"
            )
        return intent

    def _validate_llm_entities(self, parsed: dict) -> dict:
        """
        Validate LLM-extracted entities and return a clean dict.

        Only includes fields with valid values. Invalid values are silently
        discarded (the merge step will fill them from regex instead).
        """
        entities = {}

        # Section — must be a known code
        section = parsed.get("section")
        if section and section in self._valid_sections:
            entities["section"] = section

        # Department — must be valid
        department = parsed.get("department")
        if department and department in self._valid_departments:
            entities["department"] = department
            
        parameters = parsed.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        # Severity — must be valid
        severity = parameters.get("severity")
        if severity and severity.upper() in self._valid_severities:
            entities["severity"] = severity.upper()

        # Timeframe — must be a recognized keyword
        timeframe = parameters.get("timeframe")
        if timeframe and timeframe in self._valid_timeframes:
            entities["timeframe"] = timeframe
            # Convert to start_date like regex does
            days = self.TIME_KEYWORDS[timeframe]
            entities["start_date"] = (
                date.today() + timedelta(days=days)
            ).isoformat()

        # KM location — must be numeric
        km = parameters.get("km_location")
        if km is not None:
            try:
                entities["km_location"] = float(km)
            except (TypeError, ValueError):
                pass  # Discard invalid km

        # Limit — must be a positive integer
        limit = parameters.get("limit")
        if limit is not None:
            try:
                limit_int = int(limit)
                if limit_int > 0:
                    entities["limit"] = limit_int
            except (TypeError, ValueError):
                pass  # Discard invalid limit

        return entities

    def _merge_entities(self, regex_entities: dict, llm_entities: dict) -> dict:
        """
        Merge regex-detected and LLM-detected entities.

        Strategy: regex-detected values ALWAYS win for fields that regex found.
        LLM values fill in gaps that regex missed.

        This ensures deterministic pattern matches (e.g. exact section alias match)
        are never overwritten by LLM hallucinations.
        """
        merged = dict(regex_entities)  # Start with regex as the base

        for key, value in llm_entities.items():
            if key not in merged:
                # LLM detected something regex missed — use it
                merged[key] = value

        return merged

    # ─────────────────────────────────────────────────────────────
    # ORIGINAL REGEX-BASED METHODS (unchanged)
    # ─────────────────────────────────────────────────────────────

    def _detect_intent(self, command: str) -> str:
        """Detect the user's intent using pattern matching."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return intent
        return "QUERY_TASKS"  # Default intent

    def _extract_entities(self, command: str) -> dict:
        """Extract entities (section, department, dates, KM) from command."""
        entities = {}

        # Extract section — sort aliases by length (longest first)
        # so "kalyan-kasara" matches before "kalyan"
        sorted_aliases = sorted(self.SECTION_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            if alias in command:
                entities["section"] = self.SECTION_ALIASES[alias]
                entities["section_alias"] = alias
                break

        # Extract department
        for dept, keywords in self.DEPARTMENT_KEYWORDS.items():
            for kw in keywords:
                if kw in command:
                    entities["department"] = dept
                    break

        # Extract time reference
        for time_kw, days in self.TIME_KEYWORDS.items():
            if time_kw in command:
                entities["start_date"] = (date.today() + timedelta(days=days)).isoformat()
                entities["timeframe"] = time_kw
                break

        # Extract KM markers (e.g., "KM 65", "km 38.5")
        km_match = re.search(r'km\s*(\d+\.?\d*)', command, re.IGNORECASE)
        if km_match:
            entities["km_location"] = float(km_match.group(1))

        # Extract severity
        for sev in ["critical", "high", "medium", "low"]:
            if sev in command:
                entities["severity"] = sev.upper()
                break

        # Extract number (e.g., "top 5")
        num_match = re.search(r'top\s+(\d+)', command, re.IGNORECASE)
        if num_match:
            entities["limit"] = int(num_match.group(1))

        return entities

    def _map_to_api(self, intent: str, entities: dict) -> str:
        """Map intent + entities to an API endpoint."""
        api_map = {
            "QUERY_BLOCKS": "/api/blocks/available",
            "QUERY_TASKS": "/api/tasks",
            "SCHEDULE": "/api/optimizer/generate",
            "STATUS": "/api/sections/{section_id}/health",
            "OPTIMIZE": "/api/optimizer/generate",
            "PREDICT": "/api/predictions/{section_id}",
            "HELP": "/api/help",
        }
        return api_map.get(intent, "/api/tasks")

    def _generate_response(self, intent: str, entities: dict) -> str:
        """Generate a natural language response."""
        section = entities.get("section", "all sections")
        dept = entities.get("department", "")
        timeframe = entities.get("timeframe", "")

        responses = {
            "QUERY_BLOCKS": (
                f"Fetching available block windows for {section}"
                + (f" ({dept} department)" if dept else "")
                + (f" {timeframe}" if timeframe else "")
                + "..."
            ),
            "QUERY_TASKS": (
                f"Showing maintenance tasks for {section}"
                + (f" ({dept})" if dept else "")
                + (f" — {entities.get('severity', '')} severity" if entities.get('severity') else "")
                + "..."
            ),
            "SCHEDULE": (
                f"Creating block schedule for {section}"
                + (f" ({dept} work)" if dept else "")
                + ". Running AI optimizer..."
            ),
            "STATUS": (
                f"Checking health status of {section}..."
            ),
            "OPTIMIZE": (
                f"Running AI block optimization for {section}. "
                "This may take a few seconds..."
            ),
            "PREDICT": (
                f"Running predictive analysis for assets in {section}..."
            ),
            "HELP": (
                "Available commands:\n"
                "- 'Show available blocks for [section]'\n"
                "- 'Show critical tasks'\n"
                "- 'Schedule block for [task type] on [section]'\n"
                "- 'Status of [section]'\n"
                "- 'Optimize schedule for [section]'\n"
                "- 'Predict failures for [section]'\n"
                "\nYou can use Hindi or English. "
                "Example: 'Kalyan section mein pending tasks dikhao'"
            ),
        }

        return responses.get(intent, f"Processing your request for {section}...")
