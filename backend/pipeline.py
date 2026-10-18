import re

from agents import critic_chain, writer_chain
from tools import scrape_url, web_search

def run_research_pipeline(topic : str) -> dict:

    state = {}

    print("\n" + " =" * 50, flush=True)
    print("step 1 - searching the web ...", flush=True)
    print("=" * 50, flush=True)

    # Call Tavily directly. Asking an LLM agent to choose whether to call the
    # search tool adds an unnecessary model request and can look like a hang.
    state["search_results"] = web_search.invoke(
        f"Find recent, reliable and detailed information about: {topic}"
    )
    if not state["search_results"].strip():
        raise RuntimeError("Web search returned no results. Try a more specific question.")

    print("\n search result ",state['search_results'])

    #step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    urls = re.findall(r"URL:\s*(https?://\S+)", state["search_results"])
    state["scraped_content"] = ""
    for url in urls[:3]:
        try:
            state["scraped_content"] = scrape_url.invoke({"url": url})
            if state["scraped_content"].strip():
                break
        except Exception as error:
            print(f"Could not scrape {url}: {error}", flush=True)
    if not state["scraped_content"].strip():
        state["scraped_content"] = "Page text was unavailable; use the search snippets below."

    print("\nscraped content: \n", state['scraped_content'])

    #step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...", flush=True)
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\n Final Report\n",state['report'])

    #critic report 

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ", flush=True)
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])

    return state



if __name__ == "__main__":
    topic = input("\n Enter a research topic : ").strip()
    if not topic:
        raise SystemExit("Please enter a research topic.")

    try:
        run_research_pipeline(topic)
    except Exception as error:
        raise SystemExit(f"Research failed: {error}") from None
