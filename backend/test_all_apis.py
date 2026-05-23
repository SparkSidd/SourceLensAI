"""
SourceLens AI — Full API Integration Test Suite
Tests every retriever and the synthesis engine individually.
Run: python -m backend.test_all_apis
"""
import asyncio
import os
import sys
import json
import traceback

# Fix path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Print env status
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

print("=" * 70)
print("  SOURCELENS AI — FULL API INTEGRATION TEST SUITE")
print("=" * 70)
print(f"\n  Gemini API Key: {'✅ SET (' + GEMINI_KEY[:12] + '...)' if GEMINI_KEY else '❌ MISSING'}")
print(f"  Tavily API Key: {'✅ SET (' + TAVILY_KEY[:12] + '...)' if TAVILY_KEY else '❌ MISSING'}")
print(f"  Working Dir:    {os.getcwd()}")
print()

TEST_QUERY = "reinforcement learning with human feedback RLHF"
results_summary = {}


async def test_wikipedia():
    """Test Wikipedia retriever (FREE — no key needed)."""
    print("\n" + "─" * 50)
    print("  TEST 1: Wikipedia Retriever")
    print("─" * 50)
    try:
        from backend.app.sources.wikipedia import WikipediaRetriever
        retriever = WikipediaRetriever()
        results = await retriever.search(TEST_QUERY, limit=2)
        if results:
            print(f"  ✅ SUCCESS — Retrieved {len(results)} articles")
            for r in results:
                print(f"     📄 {r['title']}")
                print(f"        URL: {r['url']}")
                print(f"        Content: {r['content'][:120]}...")
                print()
            results_summary["wikipedia"] = f"✅ {len(results)} articles"
        else:
            print("  ⚠️ EMPTY — No results returned (query may not match any Wikipedia articles)")
            results_summary["wikipedia"] = "⚠️ Empty (no match)"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["wikipedia"] = f"❌ {e}"


async def test_arxiv():
    """Test arXiv retriever (FREE — no key needed)."""
    print("\n" + "─" * 50)
    print("  TEST 2: arXiv Academic Retriever")
    print("─" * 50)
    try:
        from backend.app.sources.arxiv import ArxivRetriever
        retriever = ArxivRetriever()
        results = await retriever.search(TEST_QUERY, limit=2)
        if results:
            print(f"  ✅ SUCCESS — Retrieved {len(results)} papers")
            for r in results:
                print(f"     📑 {r['title']}")
                print(f"        URL: {r['url']}")
                print(f"        Abstract: {r['content'][:120]}...")
                print()
            results_summary["arxiv"] = f"✅ {len(results)} papers"
        else:
            print("  ⚠️ EMPTY — No results returned")
            results_summary["arxiv"] = "⚠️ Empty"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["arxiv"] = f"❌ {e}"


async def test_github():
    """Test GitHub retriever (FREE — no key needed)."""
    print("\n" + "─" * 50)
    print("  TEST 3: GitHub Repositories Retriever")
    print("─" * 50)
    try:
        from backend.app.sources.github import GithubRetriever
        retriever = GithubRetriever()
        results = await retriever.search(TEST_QUERY, limit=2)
        if results:
            print(f"  ✅ SUCCESS — Retrieved {len(results)} repos")
            for r in results:
                print(f"     🔗 {r['title']}")
                print(f"        URL: {r['url']}")
                print(f"        Content: {r['content'][:120]}...")
                print()
            results_summary["github"] = f"✅ {len(results)} repos"
        else:
            print("  ⚠️ EMPTY — No results returned")
            results_summary["github"] = "⚠️ Empty"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["github"] = f"❌ {e}"


async def test_hackernews():
    """Test HackerNews retriever (FREE — no key needed)."""
    print("\n" + "─" * 50)
    print("  TEST 4: HackerNews Retriever")
    print("─" * 50)
    try:
        from backend.app.sources.hackernews import HackerNewsRetriever
        retriever = HackerNewsRetriever()
        results = await retriever.search(TEST_QUERY, limit=2)
        if results:
            print(f"  ✅ SUCCESS — Retrieved {len(results)} stories")
            for r in results:
                print(f"     💬 {r['title']}")
                print(f"        URL: {r['url']}")
                print(f"        Content: {r['content'][:120]}...")
                print()
            results_summary["hackernews"] = f"✅ {len(results)} stories"
        else:
            print("  ⚠️ EMPTY — No results returned")
            results_summary["hackernews"] = "⚠️ Empty"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["hackernews"] = f"❌ {e}"


async def test_tavily():
    """Test Tavily retriever (REQUIRES API KEY)."""
    print("\n" + "─" * 50)
    print("  TEST 5: Tavily Web Search Retriever")
    print("─" * 50)
    if not TAVILY_KEY:
        print("  ⏭️ SKIPPED — No Tavily API key set")
        results_summary["tavily"] = "⏭️ Skipped (no key)"
        return
    try:
        from backend.app.sources.tavily import TavilyRetriever
        retriever = TavilyRetriever()
        results = await retriever.search(TEST_QUERY, limit=3)
        if results:
            print(f"  ✅ SUCCESS — Retrieved {len(results)} web results")
            for r in results:
                print(f"     🌐 {r['title']}")
                print(f"        URL: {r['url']}")
                print(f"        Content: {r['content'][:120]}...")
                print()
            results_summary["tavily"] = f"✅ {len(results)} web results"
        else:
            print("  ⚠️ EMPTY — API returned no results (check key validity)")
            results_summary["tavily"] = "⚠️ Empty (check key)"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["tavily"] = f"❌ {e}"


async def test_gemini_synthesis():
    """Test Gemini LLM synthesis (REQUIRES API KEY)."""
    print("\n" + "─" * 50)
    print("  TEST 6: Gemini LLM Synthesis Engine")
    print("─" * 50)
    if not GEMINI_KEY:
        print("  ⏭️ SKIPPED — No Gemini API key set")
        results_summary["gemini_synthesis"] = "⏭️ Skipped (no key)"
        return
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = await model.generate_content_async(
            "In 2 sentences, explain what RLHF is in machine learning.",
            generation_config={"temperature": 0.2}
        )
        
        text = response.text.strip()
        if text:
            print(f"  ✅ SUCCESS — Gemini responded ({len(text)} chars)")
            print(f"     💡 Response: {text[:200]}...")
            results_summary["gemini_synthesis"] = f"✅ Working ({len(text)} chars)"
        else:
            print("  ⚠️ EMPTY — Gemini returned no text")
            results_summary["gemini_synthesis"] = "⚠️ Empty response"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["gemini_synthesis"] = f"❌ {e}"


async def test_gemini_json_mode():
    """Test Gemini JSON mode (used by QueryEngine and ContradictionDetector)."""
    print("\n" + "─" * 50)
    print("  TEST 7: Gemini JSON Mode (Query Analysis)")
    print("─" * 50)
    if not GEMINI_KEY:
        print("  ⏭️ SKIPPED — No Gemini API key set")
        results_summary["gemini_json"] = "⏭️ Skipped (no key)"
        return
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = await model.generate_content_async(
            'Classify this research query: "RLHF in LLMs". '
            'Return JSON: {"domain": "academic"|"technical"|"general", "confidence": 0.0-1.0}'
        )
        
        text = response.text.strip()
        data = json.loads(text)
        print(f"  ✅ SUCCESS — Gemini JSON mode works")
        print(f"     📊 Response: {json.dumps(data, indent=2)}")
        results_summary["gemini_json"] = "✅ Working"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        results_summary["gemini_json"] = f"❌ {e}"


async def test_config_sandbox_mode():
    """Verify SANDBOX_MODE is correctly set based on env."""
    print("\n" + "─" * 50)
    print("  TEST 8: Config / SANDBOX_MODE Check")
    print("─" * 50)
    try:
        from backend.app.core.config import SANDBOX_MODE, GEMINI_API_KEY as CFG_GEMINI, TAVILY_API_KEY as CFG_TAVILY
        print(f"  Config GEMINI_API_KEY: {'SET' if CFG_GEMINI else 'MISSING'}")
        print(f"  Config TAVILY_API_KEY: {'SET' if CFG_TAVILY else 'MISSING'}")
        print(f"  Config SANDBOX_MODE:   {SANDBOX_MODE}")
        
        if SANDBOX_MODE and CFG_GEMINI:
            print("  ⚠️ WARNING: SANDBOX_MODE is True even though Gemini key exists!")
            print("     This is because SANDBOX_MODE = not(GEMINI and TAVILY)")
            print("     But our code changes bypass this — each module checks its own key now.")
            results_summary["config"] = "⚠️ SANDBOX=True but bypassed per-module"
        elif not SANDBOX_MODE:
            print("  ✅ SANDBOX_MODE is False — all live pipelines active")
            results_summary["config"] = "✅ SANDBOX=False, all live"
        else:
            print("  ℹ️ SANDBOX_MODE is True — no API keys configured")
            results_summary["config"] = "ℹ️ SANDBOX=True, no keys"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results_summary["config"] = f"❌ {e}"


async def main():
    # Run all tests sequentially
    await test_config_sandbox_mode()
    await test_wikipedia()
    await test_arxiv()
    await test_github()
    await test_hackernews()
    await test_tavily()
    await test_gemini_synthesis()
    await test_gemini_json_mode()
    
    # Final summary
    print("\n" + "=" * 70)
    print("  FINAL RESULTS SUMMARY")
    print("=" * 70)
    for module, status in results_summary.items():
        print(f"  {module:25s} → {status}")
    print("=" * 70)
    
    all_ok = all("✅" in v for v in results_summary.values())
    if all_ok:
        print("\n  🎉 ALL SYSTEMS OPERATIONAL — Ready to launch server!\n")
    else:
        failed = [k for k, v in results_summary.items() if "❌" in v]
        if failed:
            print(f"\n  🔴 FAILURES DETECTED in: {', '.join(failed)}")
            print("     Fix these before launching the server.\n")
        else:
            print("\n  🟡 Some modules empty/skipped but no hard failures.\n")


if __name__ == "__main__":
    asyncio.run(main())
