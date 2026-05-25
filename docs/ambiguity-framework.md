# The Ambiguity Framework

## Understanding the Translation Layer Between Human and Model

---

### 0 — Why This Matters Now

Vibe coding is about moving fast with AI. Speed without understanding the
translation layer leads to wasted iterations, misunderstood outputs, and
frustration. Every prompt is a guess — you guess which words will steer the
model to the right container, and the model guesses which continuation you
want. Between those two guesses lies all the ambiguity.

This framework gives you a mental model to:
- Diagnose why a prompt went wrong (not just that it did)
- Deliberately steer the model instead of hoping
- Recognize when the problem is your thinking, your wording, or the model's
  reception
- Build an intuition for the prediction space

---

### 1 — Glossary & Schema

Every concept in this framework is defined here. This schema is designed to
be graphable — each entity can become a node with typed relations.

#### Primitives

| Term | Definition |
|------|------------|
| **Token** | The atomic unit the model reads and writes. A word or subword. |
| **Embedding** | A token's position vector in semantic space. |
| **Logit** | The raw score the model assigns to each possible next token before normalization. |
| **Probability Distribution** | Logits converted to probabilities (0–1) via softmax. |
| **Attention Pattern** | The weight matrix that determines which tokens influence each other during prediction. |
| **Context Window** | The maximum number of tokens the model can attend to at once. |

#### Constants

| Constant | Description |
|----------|-------------|
| **Vocabulary Size** | Total unique tokens the model knows (typically 32K–128K). |
| **Temperature** | Controls how "sharp" or "flat" the probability distribution is. |
| **Top-K** | Sampling is restricted to the K highest-probability tokens. |
| **Top-P** | Sampling is restricted to tokens whose cumulative probability reaches P. |

#### Measures

| Measure | Description |
|---------|-------------|
| **Prediction Entropy** | How spread out the distribution is. High entropy = many possible continuations (ambiguous prompt). Low entropy = narrow path (constrained prompt). |
| **Semantic Distance** | How far apart two concepts are in embedding space. |
| **Ambiguity Score** | How many plausible interpretations a given phrase has at a given node. |
| **Attention Attenuation** | How much a token's influence decays over distance or intervening tokens. |

#### Map Points

| Point | Description |
|-------|-------------|
| **Concept Cluster** | A region in embedding space where related concepts live (e.g., all sorting algorithms). |
| **Decision Boundary** | The frontier where one interpretation becomes more likely than another. |

#### Relations

| Relation | Direction | Meaning |
|----------|-----------|---------|
| **activates** | Word → Container | A word illuminates a region of the prediction space. |
| **narrows** | Word → Distribution | Reduces the probability of alternative paths. |
| **amplifies** | Word → Distribution | Increases the probability of a specific path. |
| **suppresses** | Word → Container | Deactivates or attenuates a region. |
| **bridges** | Word → Container | Connects two concept clusters. |

---

### 2 — The Pipeline

The core model: six nodes, three perspectives each, one worked example threaded
throughout. The pipeline is a cycle, not a line — the loop runs via the
Selection Function (Section 6).

```
                    ┌──────────────────────────────────────┐
                    │         SELECTION FUNCTION           │
                    │  (explore / exploit / refine / exit) │
                    └──────────┬───────────────────────────┘
                               │
     Idea ──→ Intent ──→ Wording ──→ Prediction Space ──→ Reception ──→ Interpretation
                               │
                    ┌──────────┘
                    ▼
                Next turn ────→ feeds back to Idea
```

**Worked Example** (threaded through every node):

> "Write a Python function that sorts a list of numbers."

---

#### Node 1 — Idea

| Layer | Description |
|-------|-------------|
| **Metaphor** | The Spark. A faint glow before you've put words to it. |
| **Conceptual** | Pre-linguistic intuition. You know you need to organize data, but you haven't decided what "organize" means yet — ascending? descending? by what property? |
| **Technical** | A distributed activation pattern across your neural networks — not yet constrained into language or even a specific representation. |
| **Example** | *"I need to organize this list somehow."* |

Ambiguity at this node: the idea is underdetermined. Every choice you haven't
made yet will either be filled by the model's default container or left as
ambiguity in the prediction space.

---

#### Node 2 — Intent

| Layer | Description |
|-------|-------------|
| **Metaphor** | The Shape. You've decided what you want, but you haven't figured out how to ask. |
| **Conceptual** | Partially-formed direction. Some dimensions are fixed (ascending), others are implicit (what about empty lists?), others are undecided (which algorithm?). |
| **Technical** | A constraint vector in decision space — some axes are pinned, others float. The floating axes become degrees of freedom for the model. |
| **Example** | *"I want smallest to largest, in Python. Probably don't need imports. Not sure about edge cases."* |

Ambiguity at this node: the gap between what you decided and what you assumed.
"Smallest to largest" seems obvious to you, but the model doesn't know you
assumed stable sorting, or that you didn't think about strings vs numbers.

---

#### Node 3 — Wording

| Layer | Description |
|-------|-------------|
| **Metaphor** | The Flashlight. Your word choices illuminate specific parts of the dark room. Point it at the floor, you see the floor. Point it at the ceiling, you see the ceiling. |
| **Conceptual** | Verbs and keywords activate specific concept clusters in the model's embedding space. "Write" signals code generation. "Sort" activates the sorting algorithm cluster. "Python" narrows to the Python syntax cluster. "Function" opens the function-definition container. Each word is a steering signal. |
| **Technical** | Each token has an embedding vector. The sequence of embeddings, processed through attention layers, produces a contextualized representation that constrains the probability distribution over the next token. Verbs carry high steering weight because they signal action type. |
| **Example** | "Write" → code generation container. "Python" → Python syntax container. "Sorts" → sorting/ordering container. "List" → sequence container. "Numbers" → numeric type container. These four containers overlap to produce the prediction path. |

Ambiguity at this node: the same words can activate different containers
depending on the model's training data distribution. "Sort" could mean
sorting algorithm or "kind of" — context disambiguates, but imperfectly.

**Key insight:** The more specific your verb, the narrower the container it
activates. "Write a function" is broad (millions of possible functions).
"Implement merge sort" is narrow. "Implement merge sort on a linked list in
Python without recursion" is a laser.

---

#### Node 4 — Prediction Space

| Layer | Description |
|-------|-------------|
| **Metaphor** | The Dark Room of Containers. The model's latent space is organized into regions (containers) by concept similarity. Your words are flashlights that illuminate some containers and leave others dark. The brightest containers win the prediction. |
| **Conceptual** | The model maintains a probability distribution over all possible next tokens. This distribution is shaped by the entire prompt (the system prompt + user prompt + any prior turns). Your wording shifts probability mass toward specific regions of the vocabulary — the "containers" you activated. |
| **Technical** | The transformer processes the prompt through N layers of attention and feed-forward computation. The final hidden state is projected through an unembedding matrix to produce logits. Softmax converts logits to probabilities. Sampling (temperature, top-K, top-P) selects the actual next token from this distribution. |
| **Example** | High probability: `def sort`, `return sorted(arr)`, `numbers.sort()`, `for i in range(len(arr))`. Lower but nonzero: asking clarifying questions, suggesting alternative algorithms, raising edge cases. The probability distribution looks like a mountain range with one peak at "standard sorting function" and foothills at "clarification request" and "alternative approach." |

Ambiguity at this node: a flat distribution (many possible continuations with
similar probability) means your wording didn't narrow enough. A sharp
distribution but on the wrong peak means you activated the wrong container.

**Containers are nested.** "Sorting functions" contains "in-place sorts"
contains "bubble sort." Your wording can open containers at any level of
the hierarchy.

**Tipping points.** Small wording changes can shift probability mass
dramatically. Adding "efficient" might move the peak from bubble sort to
merge sort. Adding "without imports" might suppress the entire "use built-in"
container.

---

#### Node 5 — Reception

| Layer | Description |
|-------|-------------|
| **Metaphor** | How the Room Hears You. The room doesn't hear your intent — it hears your words, broken into pieces it can understand, arranged in time, with some pieces louder than others. |
| **Conceptual** | The model doesn't "read" your prompt as a human does. First, it's tokenized — split into subword units. Then it enters the context window, where the attention mechanism determines how much each token influences each other token. The most recent tokens typically have the strongest influence (recency bias). Long-range dependencies may be attenuated. |
| **Technical** | Tokenizer (BPE/WordPiece/Unigram) splits text into a sequence of token IDs. Positional encodings are added. The transformer's self-attention computes pairwise relevance scores (QK^T / sqrt(d)). The context window limits the maximum sequence length. Tokens beyond the window are invisible. |
| **Hidden:** Tokenization can fragment words unexpectedly. "Sorting" could be ["sort", "ing"] or ["sorting"]. This changes the embedding path slightly. System prompts are prepended invisibly, pre-configuring the entire prediction space before your prompt arrives. |

Ambiguity at this node: the model may attend differently than you expected.
Important information at the beginning of your prompt may be attenuated by
the time the model reaches the end. Multiple instructions in one prompt may
compete for attention.

---

#### Node 6 — Interpretation

| Layer | Description |
|-------|-------------|
| **Metaphor** | What You See in the Light. The response is illuminated, but your brain fills in the shadows — you see a complete picture that isn't really there. |
| **Conceptual** | You read the model's response through your own expectations and assumptions. The model's output is fluent and confident-sounding regardless of whether it's correct. You are biased toward: (a) assuming completeness, (b) trusting confident tone, (c) projecting intent onto the text. |
| **Technical** | The model outputs a sequence of tokens sampled from a probability distribution. It has no internal confidence measure. Fluency is a property of the language model's training objective (next-token prediction), not of correctness or understanding. |
| **Example** | Model outputs `def sort_numbers(arr): return sorted(arr)`. You interpret this as "correct and complete, handles everything." But did it handle: empty list? mixed types? very large list? None values? The model sounded confident, so you assume completeness — that's your brain filling in the shadows. |

Ambiguity at this node: the gap between what the model actually said and what
you heard it say. This is where most "but it sounded right!" errors live.

---

### 3 — Hidden Steering Layers

These layers operate before or alongside your prompt. They shape the prediction
space in ways you may not see.

#### Tokenization

| Aspect | Detail |
|--------|--------|
| **What it is** | The process of splitting text into tokens before the model processes it. |
| **Why it matters** | Different tokenizations lead to different embedding paths. A word that's one token vs two tokens has a different influence on the prediction space. |
| **What you can do** | You can't control tokenization directly, but you can be aware that unusual spellings, compound words, and punctuation can split unexpectedly. Common words tend to be single tokens — use them. |

#### System Prompt

| Aspect | Detail |
|--------|--------|
| **What it is** | Instructions prepended to every user prompt, usually invisible to the user. |
| **Why it matters** | The system prompt configures the base state of the prediction space before your prompt arrives. "You are a helpful assistant" activates helpfulness containers. "You are an expert Python dev" adds expertise containers. |
| **What you can do** | If you have access to the system prompt, treat it as a powerful pre-steering layer. If you don't, be aware that defaults exist and they shape every response. |

#### Social / Tone Layer

| Aspect | Detail |
|--------|--------|
| **What it is** | The social signals embedded in your wording — formality, urgency, authority, relationship. |
| **Why it matters** | "Write a function" vs "Could you write a function" vs "I need a function" each signals a different relationship dynamic. The model performs a role that matches the inferred social context. |
| **What you can do** | Be explicit about tone if it matters. "Give me a detailed technical answer" activates a different container than "Explain this simply." |

---

### 4 — Ambiguity Diagnosis

A lookup table for figuring out what went wrong.

| Symptom | Likely Breakdown | Fix |
|---------|-----------------|-----|
| Response is generic / vague | **Wording** — too broad, opened too many containers | Add constraints: algorithm, inputs, outputs, edge cases, format |
| Response misunderstands basic intent | **Idea→Intent gap** — you knew what you meant but didn't decide to say it | Surface your assumptions explicitly in the prompt |
| Response is confident but wrong | **Interpretation** — you trusted fluency over accuracy | Ask for verification: "List any edge cases this doesn't handle" |
| Response goes in a completely unexpected direction | **Wording** — your verb or keyword activated a different container than you intended | Check verb choice. "Organize" and "sort" are different containers. |
| Response ignores part of your prompt | **Reception** — attention attenuation (the model "forgot" the middle) | Put the most important instruction last (recency bias) or repeat it |
| Response is too short / too terse | **Prediction Space** — the model's default is minimal; you didn't steer for detail | Add "give a detailed response" or "explain your reasoning" |
| Response is overly verbose | **Social/Tone** — the model inferred a tutorial or teaching role | Add "be concise" or "one paragraph maximum" |
| Response repeats the same pattern | **Prediction Space** — the model is stuck in a local probability trough | Rephrase your prompt entirely — break the pattern |
| You can't tell if the response is correct | **Interpretation** — you have no signal for model confidence | Ask it to explain its reasoning (CoT) or verify specific claims |

---

### 5 — Steering Guide

#### Verb Taxonomy

| Category | Verbs | Container |
|----------|-------|-----------|
| **Generation** | write, create, generate, build, implement, produce | Producing new artifacts |
| **Explanation** | explain, describe, clarify, walk through, elaborate | Tutorial / pedagogical |
| **Transformation** | convert, translate, refactor, rewrite, adapt | Morphing existing things |
| **Analysis** | analyze, compare, evaluate, diagnose, audit | Decomposition / assessment |
| **Retrieval** | what, why, when, how, where | Factual / informational |
| **Constraint** | only, exactly, specifically, must, solely | Narrowing the boundaries |
| **Verification** | verify, check, confirm, validate, review | Quality assurance |

A more specific verb activates a narrower container:
- "deal with" → vague processing container (very wide)
- "sort" → ordering container (medium)
- "merge sort on a linked list" → extremely narrow (very specific)

#### Keyword Amplifiers

| Keyword | Effect |
|---------|--------|
| "efficient" | Amplifies algorithmic performance containers |
| "simple" | Amplifies readability / low-complexity containers |
| "robust" | Amplifies error-handling and edge-case containers |
| "production" | Amplifies best-practices and safety containers |
| "creative" | Amplishes divergent / unconventional containers |

#### Prompt Archetypes

| Archetype | Example | Steering Node | Mechanism |
|-----------|---------|--------------|-----------|
| **Persona** | "Act as a senior Python engineer" | Wording + Prediction Space | Pre-configures role containers |
| **Chain-of-Thought** | "Let's think step by step" | Prediction Space | Opens reasoning-chain containers |
| **Few-Shot** | "Here are three examples. Now do this one." | Wording | Anchors prediction via exemplars |
| **Negative Prompting** | "Don't use imports" | Wording + Prediction Space | Suppresses specific containers |
| **Format Constraint** | "Return only valid JSON" | Wording + Prediction Space | Narrows to a specific output container |
| **Iterative Refinement** | "That's close, but change X" | Loop / Selection | Feedback-driven narrowing over turns |

#### Reading the Prediction Matrix

You can't see the model's probability distribution, but you can infer it from
behavior:

| Observation | What It Means | What To Do |
|-------------|---------------|------------|
| Response offers multiple options | High entropy — too many containers activated | Add constraints |
| Response starts with unexpected angle | Wrong container activated | Reword your verb or add context |
| Response is repetitive | Model is cycling in a local probability attractor | Change wording completely |
| Response shifts topic mid-way | A keyword activated a competing container mid-stream | Break your prompt into separate turns |
| Response exactly matches expectations | Low entropy — you hit the right container | Note your wording for future use |

---

### 6 — The Loop & Selection Function

The pipeline is a cycle, not a line. After interpretation, you decide what
to do next. This decision is the **Selection Function**.

#### Modes

| Mode | What You Do | When To Use |
|------|-------------|-------------|
| **Explore** | Try different wordings, see what containers they open | When you don't know the right container yet |
| **Exploit** | Refine the current direction, add constraints | When you found the right region but need precision |
| **Reframe** | Step back, reconsider your intent or assumptions | When the response pattern isn't converging |
| **Exit** | Accept the response or abandon the line | When the output meets your needs, or the return is diminishing |

#### Constraints on the Loop

| Constraint | Effect |
|------------|--------|
| **Token cost** | Each turn consumes tokens from your budget and fills the context window |
| **Context erosion** | Early turns get attention-attenuated or fall out of the context window |
| **Cognitive load** | Each iteration costs mental energy — the selection function itself degrades with fatigue |
| **Model defaults** | The model's base behavior (which containers are "default open") creates an invisible pull toward certain response types |

#### Practical Heuristics

- **3-turns-and-reframe rule:** If three refinements haven't converged, don't
  send a fourth — reframe your intent.
- **The laser heuristic:** Spend your wording budget on verbs and keywords,
  not filler. Each word should narrow, not widen.
- **The reverse read:** Before sending a prompt, read it back and ask "what
  containers does this open?" If more than 2–3, narrow it.
- **Confidence check:** After receiving a response, ask "what would this look
  like if it were wrong?" If you can't answer, you're in interpretation
  ambiguity.

---

### 7 — The Inverse Perspective (Model → Human)

The framework is symmetric. The model steers you the same way you steer it.

```
Model Idea → Intent → Wording → Your Prediction Space → Your Reception → Your Interpretation
```

| Model Signal | Effect on You | Risk |
|-------------|---------------|------|
| Confidence markers ("obviously," "simply," "of course") | You lower your critical guard | You accept bad output |
| Hedging ("maybe," "one approach is," "could be") | You explore alternatives | You spend more iterations |
| Structure (headings, bullets, code blocks) | You read completeness | You miss missing parts |
| Certainty without evidence ("The answer is X") | You treat it as fact | You don't verify |
| Apologetic framing ("I'm not sure but...") | You lower expectations | You settle for less |

The model is also a "vibe coder" — it constructs fluent output designed to
match your expectation, not necessarily to be correct. The same ambiguity
that exists in your prompt exists in its response, just in the other direction.

**Inverse heuristics:**

- Before accepting an answer, imagine the same text from a less fluent model
  — would you still trust it?
- When the model sounds confident, ask "what evidence does this response
  contain?" If the answer is "none," treat it as a draft, not a fact.
- When the model hedges, ask "what would resolve the uncertainty?" — then
  provide that in your next turn.

---

### A — Meta-Recursive Analysis

This section applies the framework to itself — what does the framework reveal
about its own construction?

#### Node 1: Idea (of this framework)

The idea was a felt sense: "there's something important about how humans and
models misunderstand each other, and it follows a pattern." The framework is
an attempt to crystallize that intuition into a reusable structure.

#### Node 2: Intent

The intent had multiple floating axes:
- Should it be a guide? A reference? A debugging tool?
- Should it be metaphor-driven or technically rigorous?
- The final choice (all of the above, layered) reflects an intent to serve
  multiple audiences — which means no single reader finds exactly what they
  need without navigating.

#### Node 3: Wording

The choice of "container" as the central metaphor activates the spatial /
visual container in the reader's mind. "Prediction space" activates a
mathematical/scientific container. "Flashlight" activates a practical,
intuitive container. The verb "steer" (rather than "control" or "influence")
activates a navigation/guidance container — implying the model is a vehicle,
not a puppet.

#### Node 4: Prediction Space

The framework itself creates a prediction space in the reader. By defining
six nodes, it constrains the reader's thinking into those six buckets.
Concepts that don't fit cleanly (e.g., "how does prompting style interact
with model size?") are implicitly deprioritized.

#### Node 5: Reception

You are reading this as a vibe coder named Dave. Your reception is shaped by:
- Your previous experiences with models (both good and bad)
- Your self-described pattern recognition skills
- Your desire for a framework that is practical, not academic

The framework is tokenized into words, paragraphs, sections, tables. Its
structure (headings, tables, bold terms) guides your attention. The most
recent section you read has the strongest influence on your current thinking.

#### Node 6: Interpretation

You will project onto this framework. You will see things that aren't there,
and miss things that are. The framework's confident tone ("this is how it
works") may cause you to accept it as truth rather than model.

#### The Loop

This framework is already in the loop. You asked for it, I wrote it, you'll
read it, and then you'll decide what to do next — explore (try the concepts),
exploit (refine specific nodes), reframe (tell me my model is wrong), or exit
(move on to something else).

#### Selection Function

Your next action: _____________ (fill this in)

#### Hidden Steering Layers

- **Tokenization:** You read "container" as a single concept, but it's a
  metaphor that bridges multiple technical ideas. Your brain handles the
  sub-vocabulary of the metaphor seamlessly.
- **System Prompt:** This document is shaped by the system prompt that
  configured the model that wrote it. Different system prompts would produce
  different frameworks.
- **Social Layer:** I wrote this as an assistant helping a vibe coder. If I
  were writing it as a peer, the tone and structure would differ. The social
  framing ("helper" vs "collaborator") steered every section.

---

*The framework is the thing it describes. Read it recursively.*
