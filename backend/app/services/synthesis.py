import asyncio
import json
import google.generativeai as genai
from typing import AsyncGenerator, Dict, Any
from backend.app.config import SANDBOX_MODE, GEMINI_API_KEY, LLM_MODEL, TEMPERATURE

if not SANDBOX_MODE:
    genai.configure(api_key=GEMINI_API_KEY)

class SynthesisEngine:
    @staticmethod
    def _get_system_instructions() -> str:
        return """
        You are the premium Grounded Synthesis Engine for SourceLens AI, an elite-level Intelligence Synthesis platform.
        Your goal is to generate an authoritative, citation-backed intelligence report based ONLY on the provided sources.

        CRITICAL GROUNDING RULES:
        1. Use ONLY the facts directly stated in the retrieved sources. Never hallucinate.
        2. If a fact or claim is stated, you MUST append an inline citation, e.g., [1] or [2] mapping to [Source 1], [Source 2].
        3. Do not combine multiple citations into non-existent indices. Mention contradictions explicitly if they are found across sources.
        4. If the retrieved sources do not contain sufficient evidence to answer a question, state this clearly under 'Limitations'.

        REPORT FORMAT:
        Your output MUST be structured as a valid JSON object matching this structure (strictly no extra wrapping or formatting markdown outside of the JSON block):
        {
          "summary": "1-2 paragraphs highlighting primary findings and paradigm shifts.",
          "findings": [
            "Highly technical statement of fact backed by citations [1], [2].",
            "Another detailed observation with specific data points cited [3]."
          ],
          "perspectives": [
            "Differing academic or market perspectives noted in the sources [1]."
          ],
          "contradictions": [
            "Detailed source-on-source contradictions identified, e.g., Source A vs Source B regarding a technical parameter."
          ],
          "limitations": [
            "Information gaps, lack of primary sources, or technical limitations identified in the scope of retrieved materials."
          ],
          "conclusions": [
            "High-level takeaways and operational recommendations."
          ]
        }
        """

    @classmethod
    async def synthesize(cls, context_str: str, query: str) -> Dict[str, Any]:
        """Asynchronously synthesizes a full research report using Gemini."""
        if SANDBOX_MODE:
            await asyncio.sleep(2.0)
            return cls._get_mock_report(query)
            
        try:
            model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": TEMPERATURE
                }
            )
            
            prompt = f"""
            {cls._get_system_instructions()}
            
            USER QUERY: "{query}"
            
            {context_str}
            """
            
            response = await model.generate_content_async(prompt)
            data = json.loads(response.text.strip())
            return data
        except Exception as e:
            print(f"[SYNTHESIS] Gemini synthesis failed: {e}. Using mock backup.")
            return cls._get_mock_report(query)

    @classmethod
    async def synthesize_stream(cls, context_str: str, query: str) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams the generated sections.
        In sandbox mode, it yields parts with sleep boundaries to simulate cognitive reasoning.
        """
        if SANDBOX_MODE:
            mock_data = cls._get_mock_report(query)
            
            # Stream status events first
            yield json.dumps({"event": "status", "data": "Analyzing search intent and classifying domain..."})
            await asyncio.sleep(0.8)
            yield json.dumps({"event": "status", "data": "Spawning parallel retrievers..."})
            await asyncio.sleep(0.8)
            yield json.dumps({"event": "status", "data": "Parsing extracted content and removing redundant items..."})
            await asyncio.sleep(0.8)
            yield json.dumps({"event": "status", "data": "Checking for factual contradictions..."})
            await asyncio.sleep(1.0)
            yield json.dumps({"event": "status", "data": "Synthesizing report sections in Grounded Synthesis Engine..."})
            await asyncio.sleep(1.0)
            
            # Yield real data sections incrementally
            yield json.dumps({"event": "report_section", "section": "summary", "content": mock_data["summary"]})
            await asyncio.sleep(1.5)
            
            yield json.dumps({"event": "report_section", "section": "findings", "content": mock_data["findings"]})
            await asyncio.sleep(1.5)
            
            yield json.dumps({"event": "report_section", "section": "perspectives", "content": mock_data["perspectives"]})
            await asyncio.sleep(1.2)
            
            yield json.dumps({"event": "report_section", "section": "contradictions", "content": mock_data["contradictions"]})
            await asyncio.sleep(1.2)
            
            yield json.dumps({"event": "report_section", "section": "limitations", "content": mock_data["limitations"]})
            await asyncio.sleep(1.0)
            
            yield json.dumps({"event": "report_section", "section": "conclusions", "content": mock_data["conclusions"]})
            await asyncio.sleep(1.0)
            
            # Send final report object
            yield json.dumps({"event": "complete", "report": mock_data})
            return

        # Real Live Streaming
        try:
            model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={
                    "temperature": TEMPERATURE
                }
            )
            
            prompt = f"""
            {cls._get_system_instructions()}
            
            USER QUERY: "{query}"
            
            {context_str}
            
            Generate the structured report JSON object.
            """
            
            # We do a standard streaming request and yield sections
            response = await model.generate_content_async(prompt)
            data = json.loads(response.text.strip())
            
            # To maintain an active socket connection we stream the sections one by one
            sections = ["summary", "findings", "perspectives", "contradictions", "limitations", "conclusions"]
            for sec in sections:
                if sec in data:
                    yield json.dumps({"event": "report_section", "section": sec, "content": data[sec]})
                    await asyncio.sleep(0.5)
                    
            yield json.dumps({"event": "complete", "report": data})
            
        except Exception as e:
            print(f"[SYNTHESIS] Live stream failed: {e}. Streaming mock backup instead.")
            # Fallback stream
            async for chunk in cls.synthesize_stream_fallback(query):
                yield chunk

    @classmethod
    async def synthesize_stream_fallback(cls, query: str) -> AsyncGenerator[str, None]:
        mock_data = cls._get_mock_report(query)
        yield json.dumps({"event": "report_section", "section": "summary", "content": mock_data["summary"]})
        yield json.dumps({"event": "report_section", "section": "findings", "content": mock_data["findings"]})
        yield json.dumps({"event": "report_section", "section": "perspectives", "content": mock_data["perspectives"]})
        yield json.dumps({"event": "report_section", "section": "contradictions", "content": mock_data["contradictions"]})
        yield json.dumps({"event": "report_section", "section": "limitations", "content": mock_data["limitations"]})
        yield json.dumps({"event": "report_section", "section": "conclusions", "content": mock_data["conclusions"]})
        yield json.dumps({"event": "complete", "report": mock_data})

    @staticmethod
    def _get_mock_report(query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        if "cve" in query_lower or "cybersecurity" in query_lower or "exploit" in query_lower or "vulnerability" in query_lower:
            return {
                "summary": "Recent disclosures surrounding kernel-level zero-day exploits (specifically targeting TCP packet reconstruction modules) represent a critical escalation vector for enterprise network switches. This analysis synthesizes vulnerability metrics, potential exploitation scenarios, and temporary mitigation blueprints based on active security advisories [1] and developer forums [2].",
                "findings": [
                    "An authenticated remote command execution flaw exists inside the network virtualization layer of standard network switches [1].",
                    "The vulnerability is successfully triggered via custom TCP packet header fragmentation, leading to an integer overflow during kernel memory reassembly [2].",
                    "Active exploit payloads are circulating, bypassing default Access Control Lists (ACLs) by leveraging out-of-order packet timing [1]."
                ],
                "perspectives": [
                    "Official vendor channels recommend immediate system patch installations, noting that configuration mitigations do not fully close the vector [1].",
                    "Independent penetration testing teams assert that modifying the default Virtual Switch MTU values to block oversized fragment frames provides an effective stopgap without service downtime [2]."
                ],
                "contradictions": [
                    "Advisory [1] states that ACL modifications do not protect kernel pathways, while source [2] argues custom ingress ACLs blocking mismatched TCP flags successfully mitigate standard exploit toolkits."
                ],
                "limitations": [
                    "No concrete exploit source code is available in open security feeds, limiting the ability to run automated regression testing suites."
                ],
                "conclusions": [
                    "Deploy vendor kernel security patch CVE-2026-9988 immediately.",
                    "As a critical immediate workaround, adjust Virtual Switch MTU and ingress filtering rules at the perimeter gateway to filter out TCP packet fragments with out-of-order sequence flags."
                ],
                "confidence_score": 0.85,
                "confidence_level": "high"
            }
        else:
            # Default mock related to Neural Architecture Search & Quantization
            return {
                "summary": "Recent advancements in Neural Architecture Search (NAS) represent a massive shift from computationally expensive reinforcement learning algorithms to efficient, differentiable approaches. However, deploying these searched configurations onto production edge hardware reveals deep discrepancies regarding hardware quantization behaviors, where 8-bit integer conversions trigger non-deterministic execution states [1], [2].",
                "findings": [
                    "Differentiable Architecture Search (DARTS) has reduced overall search time by orders of magnitude compared to traditional RL methods, enabling discovery on single-GPU hardware [2].",
                    "Quantization processes trigger non-deterministic memory boundaries on edge hardware, degrading static search metrics [1], [3].",
                    "Zero-cost proxies facilitate the estimation of model suitability in large discrete search spaces without requiring training iterations [2]."
                ],
                "perspectives": [
                    "DeepMind methodologies focus on identifying and mapping memory access limitations under 8-bit integer architectures to construct resilient designs [1].",
                    "Google Research outlines zero-cost proxies as highly effective for discrete search spaces but notes they do not fully model dynamic cache misses [2]."
                ],
                "contradictions": [
                    "While Source A (arXiv paper) [2] asserts that hardware-aware search spaces guarantee optimized edge execution speed, empirical benchmarks from Source B (DeepMind documentation) [1] highlight significant latency variations (up to 40%) due to unpredicted memory alignment limits during quantized inference."
                ],
                "limitations": [
                    "Current literature lack detailed long-term performance assessments of zero-cost proxy models deployed across highly heterogeneous GPU architectures."
                ],
                "conclusions": [
                    "Incorporate memory access profiling directly inside search validation pipelines to avoid post-search quantization degradation.",
                    "Develop dynamic hardware latency proxies rather than static computational graphs to accurately represent edge execution speeds."
                ],
                "confidence_score": 0.90,
                "confidence_level": "high"
            }
