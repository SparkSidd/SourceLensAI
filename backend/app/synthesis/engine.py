import json
import asyncio
import re
from typing import AsyncGenerator, Dict, Any, List

from backend.app.core.config import SANDBOX_MODE, GEMINI_API_KEY, LLM_MODEL, TEMPERATURE
from backend.app.prompts.prompts import REPORT_SYNTHESIS_PROMPT

class GroundedSynthesisEngine:

    @classmethod
    async def synthesize_stream(cls, context: str, query: str) -> AsyncGenerator[str, None]:
        """
        Asynchronously stream synthesized grounded reports.
        Yields JSON string blocks detailing incremental sections or pipeline updates.
        """
        if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
            async for chunk in cls._stream_context_aware_report(query, context):
                yield chunk
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(LLM_MODEL)

            prompt = REPORT_SYNTHESIS_PROMPT.format(
                context=context,
                query=query
            )

            response_stream = await model.generate_content_async(
                prompt,
                generation_config={"temperature": TEMPERATURE},
                stream=True
            )

            accumulated_text = ""
            sections = ["summary", "findings", "perspectives", "contradictions", "limitations", "conclusions"]

            yield json.dumps({"event": "status", "data": "Synthesizing intelligence sections..."})

            async for chunk in response_stream:
                if chunk.text:
                    accumulated_text += chunk.text

                    for sec in sections:
                        tag = f"[{sec.upper()}]"
                        next_tags = [f"[{s.upper()}]" for s in sections if s != sec]

                        if tag in accumulated_text:
                            parts = accumulated_text.split(tag)
                            if len(parts) > 1:
                                main_block = parts[1]
                                for nt in next_tags:
                                    if nt in main_block:
                                        main_block = main_block.split(nt)[0]

                                clean_block = cls._clean_section_block(sec, main_block)
                                yield json.dumps({
                                    "event": "report_section",
                                    "metadata": {
                                        "section": sec,
                                        "content": clean_block
                                    }
                                })

            final_report = cls._parse_final_report(accumulated_text)
            yield json.dumps({
                "event": "complete",
                "report": final_report
            })

        except Exception as e:
            print(f"[SYNTHESIS ENGINE] LLM generation failed: {e}. Using context-aware fallback.")
            async for chunk in cls._stream_context_aware_report(query, context):
                yield chunk

    @classmethod
    def _clean_section_block(cls, sec: str, text: str):
        """Parse and format section text based on expected output type."""
        text = text.strip()
        text = re.sub(r'\[[A-Z_]+\]', '', text).strip()

        if sec in ["findings", "perspectives", "limitations", "conclusions"]:
            lines = text.split("\n")
            bullets = []
            for line in lines:
                line = line.strip().lstrip("-").lstrip("*").lstrip("1234567890.").strip()
                if line:
                    bullets.append(line)
            return bullets if bullets else [text]
        return text

    @classmethod
    def _parse_final_report(cls, full_text: str) -> Dict[str, Any]:
        """Compile structured report dictionary from raw streamed text."""
        sections = ["summary", "findings", "perspectives", "contradictions", "limitations", "conclusions"]
        report: Dict[str, Any] = {}

        for sec in sections:
            tag = f"[{sec.upper()}]"
            next_tags = [f"[{s.upper()}]" for s in sections if s != sec]

            if tag in full_text:
                block = full_text.split(tag)[1]
                for nt in next_tags:
                    if nt in block:
                        block = block.split(nt)[0]
                report[sec] = cls._clean_section_block(sec, block)
            else:
                report[sec] = [] if sec != "summary" else ""

        return report

    # ──────────────────────────────────────────────────────────────
    #  Context-Aware Fallback Synthesis (no LLM required)
    # ──────────────────────────────────────────────────────────────

    @classmethod
    def _parse_source_blocks(cls, context: str) -> List[Dict[str, str]]:
        """
        Parse the structured context string into individual source dictionaries.
        Expected context format per source block:
            Source [N]
            Title: ...
            URL: ...
            Content: ...
        """
        sources = []
        if not context or not context.strip():
            return sources

        # Split on 'Source [' pattern to isolate each block
        raw_blocks = re.split(r'Source \[\d+\]', context)

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            title = ""
            url = ""
            content = ""

            # Extract Title
            title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', block)
            if title_match:
                title = title_match.group(1).strip()

            # Extract URL
            url_match = re.search(r'URL:\s*(.+?)(?:\n|$)', block)
            if url_match:
                url = url_match.group(1).strip()

            # Extract Content (everything after "Content:" to end of block)
            content_match = re.search(r'Content:\s*(.+)', block, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()

            if title or content:
                sources.append({
                    "title": title,
                    "url": url,
                    "content": content
                })

        return sources

    @classmethod
    def _extract_key_sentences(cls, text: str, max_sentences: int = 3) -> List[str]:
        """Extract the most informative sentences from a content block."""
        if not text:
            return []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short or noisy sentences
        useful = []
        for s in sentences:
            s = s.strip()
            # Skip very short fragments, URLs, or metadata-only lines
            if len(s) < 25:
                continue
            if s.startswith("http") or s.startswith("www."):
                continue
            # Prefer sentences with actual information density
            useful.append(s)

        return useful[:max_sentences]

    @classmethod
    def _build_report_from_sources(cls, query: str, sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Build a structured research report by extracting and organizing
        real content from the retrieved sources. No LLM needed.
        """
        num_sources = len(sources)

        # ── Summary ──
        # Build from first 2 sources' key sentences
        summary_parts = [f"Analysis of '{query}' across {num_sources} retrieved sources reveals the following insights."]
        for i, src in enumerate(sources[:3]):
            key = cls._extract_key_sentences(src["content"], max_sentences=1)
            if key:
                citation = f"[{i+1}]"
                # Truncate very long sentences
                sentence = key[0][:300]
                if not sentence.endswith("."):
                    sentence = sentence.rsplit(" ", 1)[0] + "."
                summary_parts.append(f"{sentence} {citation}")
        summary = " ".join(summary_parts)

        # ── Findings ──
        # Pull key sentences from each source as distinct findings
        findings = []
        for i, src in enumerate(sources):
            sentences = cls._extract_key_sentences(src["content"], max_sentences=2)
            citation = f"[{i+1}]"
            for s in sentences:
                s = s[:350]
                if not s.endswith("."):
                    s = s.rsplit(" ", 1)[0] + "."
                findings.append(f"{s} {citation}")
        # Deduplicate similar findings (simple length-based dedup)
        seen_prefixes = set()
        deduped_findings = []
        for f in findings:
            prefix = f[:60].lower()
            if prefix not in seen_prefixes:
                seen_prefixes.add(prefix)
                deduped_findings.append(f)
        findings = deduped_findings[:6]  # Cap at 6 findings

        # ── Perspectives ──
        # Derive from source types and titles
        perspectives = []
        source_types_seen = set()
        for src in sources:
            url = src.get("url", "")
            title = src.get("title", "")
            if "arxiv.org" in url and "academic" not in source_types_seen:
                source_types_seen.add("academic")
                perspectives.append(f"Academic research (arXiv) examines '{title[:80]}', contributing peer-reviewed evidence to this topic.")
            elif "wikipedia.org" in url and "encyclopedia" not in source_types_seen:
                source_types_seen.add("encyclopedia")
                perspectives.append(f"Encyclopedic sources (Wikipedia) provide broad foundational context via '{title[:80]}'.")
            elif "github.com" in url and "engineering" not in source_types_seen:
                source_types_seen.add("engineering")
                perspectives.append(f"Open-source engineering implementations (GitHub) demonstrate practical applications through '{title[:80]}'.")
            elif ("news.ycombinator" in url or "hackernews" in url.lower()) and "community" not in source_types_seen:
                source_types_seen.add("community")
                perspectives.append(f"Developer community discussions (Hacker News) surface real-world opinions and debates around this topic.")
            elif "web" not in source_types_seen:
                source_types_seen.add("web")
                domain = url.replace("https://", "").replace("http://", "").split("/")[0] if url else "web sources"
                perspectives.append(f"Web sources ({domain}) contribute applied research and industry analysis on '{query[:60]}'.")
        if not perspectives:
            perspectives = [f"Multiple source types contribute diverse viewpoints on '{query[:80]}'."]

        # ── Limitations ──
        limitations = []
        if num_sources < 4:
            limitations.append(f"Only {num_sources} sources were retrieved, which may limit the breadth of this analysis.")
        has_arxiv = any("arxiv.org" in s.get("url", "") for s in sources)
        has_wiki = any("wikipedia.org" in s.get("url", "") for s in sources)
        if not has_arxiv:
            limitations.append("No peer-reviewed academic papers (arXiv) were found, limiting scientific rigor verification.")
        if not has_wiki:
            limitations.append("No encyclopedic baseline (Wikipedia) was available for foundational context.")
        limitations.append("This report was generated using extractive synthesis without LLM reasoning. Results reflect direct source content without inferential analysis.")

        # ── Conclusions ──
        conclusions = []
        if findings:
            conclusions.append(f"Based on {num_sources} retrieved sources, '{query[:60]}' is an actively documented topic with material available across multiple domains.")
        for i, src in enumerate(sources[:2]):
            title = src.get("title", "")[:80]
            if title:
                conclusions.append(f"Source '{title}' provides key reference material and should be reviewed for detailed information [{i+1}].")
        conclusions.append("For deeper analysis, re-run this query with LLM synthesis enabled to generate inferential insights across sources.")

        return {
            "summary": summary,
            "findings": findings,
            "perspectives": perspectives,
            "contradictions": [],
            "limitations": limitations,
            "conclusions": conclusions
        }

    @classmethod
    async def _stream_context_aware_report(cls, query: str, context: str = "") -> AsyncGenerator[str, None]:
        """
        Fallback synthesis that builds a real report from actual retrieved source content.
        Parses the context string, extracts titles, URLs, and key sentences,
        then assembles a structured report grounded in the real data.
        """
        sources = cls._parse_source_blocks(context)

        if not sources:
            # No context at all — yield a minimal informational message
            yield json.dumps({"event": "status", "data": "ORION: No source context available. Generating minimal report..."})
            await asyncio.sleep(0.3)
            report = {
                "summary": f"No sources were retrieved for '{query}'. Please verify your query or check API connectivity.",
                "findings": [],
                "perspectives": [],
                "contradictions": [],
                "limitations": ["No external sources were available for analysis."],
                "conclusions": [f"Retry the query '{query[:60]}' or broaden search terms to retrieve actionable sources."]
            }
            yield json.dumps({"event": "complete", "report": report})
            return

        # Build real report from actual sources
        report = cls._build_report_from_sources(query, sources)

        # Stream sections with realistic pacing
        yield json.dumps({"event": "status", "data": f"ORION: Synthesizing report from {len(sources)} retrieved sources (extractive mode)..."})
        await asyncio.sleep(0.4)

        yield json.dumps({"event": "report_section", "metadata": {"section": "summary", "content": report["summary"]}})
        await asyncio.sleep(0.3)

        yield json.dumps({"event": "status", "data": "ORION: Grounding claims with source citations..."})
        yield json.dumps({"event": "report_section", "metadata": {"section": "findings", "content": report["findings"]}})
        await asyncio.sleep(0.3)

        yield json.dumps({"event": "report_section", "metadata": {"section": "perspectives", "content": report["perspectives"]}})
        await asyncio.sleep(0.25)

        if report["contradictions"]:
            yield json.dumps({"event": "status", "data": "ORION: Scanning cross-reference contradictions..."})
            yield json.dumps({"event": "report_section", "metadata": {"section": "contradictions", "content": report["contradictions"]}})
            await asyncio.sleep(0.3)

        yield json.dumps({"event": "report_section", "metadata": {"section": "limitations", "content": report["limitations"]}})
        await asyncio.sleep(0.2)

        yield json.dumps({"event": "report_section", "metadata": {"section": "conclusions", "content": report["conclusions"]}})
        await asyncio.sleep(0.15)

        yield json.dumps({
            "event": "complete",
            "report": report
        })
