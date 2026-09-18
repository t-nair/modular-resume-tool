# modular-resume-tool
Brain dump here is the user flow.

The user inputs a copy pasted job posting (**Flow B**) and uploads their resume (LaTeX for P0) (**Flow A**)

## Flow A (this happens on signup basically)
1. The user uploads their resume(s). This resume is parsed and converted into a modular LaTeX file in the backend.
2. They also have to input some things like their preferences for the resume - how many pages, other limits that I can't think of rn, this also might ruin the font and formatting if they don't select a preference for that but selecting additional preferences beyond page numbers and section limits is P1 material
3. We use a model (likely a NER model? though I'm open to feedback on this one not sure how best to parse to keep costs down and reduce chances of hallucination) to identify two main things: sections and entities.
* **Sections** are parts of the resume like headings (Education, Skills, Experience, etc.) and are parsed and stored in a DB. They are classified into two types: mutable and immutable. A _mutable_ section is one that changes depending on the job posting, immutable sections don't change. Examples of _immutable_ sections would be things like Education (for P0 we're keeping the Activities portion and other bullets for Education immutable). Mutable sections are basically everything else.
* Once sections are identified and stored, we identify entities. **Entities** are the subheadings, so the various positions that are listed under someone's Experience section are each entities with details associated with them.
3. The identified entities are vectorized and stored in a database (what model? what database? idk.) so that we can search against them how exciting!!!!!!

## Flow B (this is repeated for each posting)
1. The job posting is parsed using a keyword extraction model like GLiNER 2 to get core skills, hard requirements, and what you'll learn from the position.
2. We use these keywords to run a vector search on the DB of the user's entities to find top k matches for each section. How convenient
3. With these surfaced matches, the user can select the best entities for each section (which they also need to select maybe or is that too much choice) for that position
* They can also choose beyond the matches but they'll need to search for specific entities (this will be regular search)
4. We then render the new LaTeX resume! Download options are .pdf or the LaTeX project file (button to export to OverLeaf in P1)
5. We also have an optional **Flow C**

## Flow C - Scoring System
1. We input the resume into Hackerrank ATS and also use keyword matching/regular code to calculate some scores. User has the option to upload a cover letter for that position too.
2. We feed the job description, Hackerrank/custom scores, and cover letter draft into an LLM (or maybe some other model idk) and have it calculate % likelihood of a response, output an optimized cover letter, and also some enhancement ideas for the resume or profile in general (like a project they can do, etc.)

The purpose of the scoring system is to use on positions that are your top choice, since it's more expensive to run.

## Current Confusions/Notes
* Very important that the LaTeX is modular though I think this is going to be annoying to debug but it might be ok
* How are we going to model the entities for sections like Skills (where it's more of a list of keywords) vs. Experience (where it's richer text?
* Should sections be vectorized as well? Do we really need to search sections?
* Scoring the bullets/rich descriptions of the entities against a rubric (keyword recognition on the parsed text) would be goated but might be better off for P1
* All of the other things in my dump
