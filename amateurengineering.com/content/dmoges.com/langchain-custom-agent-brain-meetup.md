---
Title: Building a Custom Agent with LangChain
Date: 2026-06-10T20:00:00+10:00
Summary: My LangChain talk from the BRAIN AI meetup at the Ballarat Hackerspace - building a custom agent live, from a chatbot all the way down to a hand-rolled tool loop.
Tags: langchain, ai, agents, llm, brain, ballarat, talk
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

I gave this talk at the [BRAIN AI Applications and Tooling Meetup](https://ballarathackerspace.tidyhq.com/public/schedule/events/85415-brain-ai-applications-and-tooling-meetup) at the Ballarat Hackerspace on 10 June 2026.
I wanted to introduce LangChain, as a means to building custom agents in Python.
I've been coding with it for a client project for a while now, which has allowed me to do things that aren't easy to do with a standard agent: things like validation, cross-source checking, and so on, while doing the "main" thread.

Additionally, my goal for the talk (achieved!) was to show the low-level "what does it mean when we say an agent is tool-calling?".
This was because they aren't - they are "asking" to use tools by returning output that specifies they want to do that.

So, an agent is an LLM in a loop, where the output is parsed and sometimes interpreted to mean "I, as the agent, want to do this action" now.
The orchestrating code then does the tool calling.

## The "Lang*" family

People say "LangChain" to mean five different things, so the first job is clearing that up.
As I was targeting **LangChain 1.0** (GA'd 22 October 2025), I mentioned that LangChain had previously had a bit of a reputation for changing interfaces constantly, inconsistent releases, and being hard to work with in production software. 
That looks to be cleared up. 
If you are interested in LangChain, I strongly recommend you go straight for the latest release, and ignore `langchain-classic`.


| Name | What it actually is | When you touch it |
|------|--------------------|--------------------|
| **LangChain** | High-level building blocks + `create_agent`. The fast path. | Building most apps; prototyping. |
| **LangGraph** | The low-level runtime: agents as a state machine (nodes, edges, loops, persistence). LangChain 1.0 *runs on it*. | When you need branching, cycles, durable state, multi-agent. |
| **LangSmith** | Observability/tracing/eval SaaS. Not required to run anything. | Debugging and evaluating in production. |
| **LangFlow** | Drag-and-drop visual builder. | Non-coders / fast demos. |

Basically, **LangChain is built *on* LangGraph**.
For the purposes of my talk, I ignored LangSmith and LangFlow.
When getting into this field, you start with LangChain, and move to LangGraph when your needs get more complicated than you'd like.


## The standard interface

LangChain's real selling point is the provider-agnostic interface: one line gets you a model, and you just swap models with a parameter change. 
We'll see that later.

The below code assumes an `ANTHROPIC_API_KEY` environment variable is set.

```python
from langchain.chat_models import init_chat_model

model = init_chat_model('claude-sonnet-4-6', model_provider='anthropic')
response = model.invoke('In one sentence, how awesome is Ballarat?')
print(response.content)
```

```
Ballarat is an incredibly awesome city, brimming with rich gold rush history,
stunning Victorian architecture, vibrant arts and culture, and a warm, welcoming
community that makes it one of regional Australia's most charming destinations.
```

Thank you for coming to my talk.

Seriously, now we have a model as a building block, we can start thinking about how to interface with that model, and what we can do with this simple function call.

## A chatbot with memory

The next level up is to build a chatbot.
This is the above code in a loop, but we need to keep memory/context about the conversation so far.
In LangChain, memory is just a list of messages. 
There are a few types, which we'll see soon, but to add more to the context, we just append a new message to the list of messages.
Compacting and other context-cleaning methods are just operations on this list.

In the below code, we wrap `invoke` in a function to automatically update the context.
This isn't needed, but if you don't do something, you'll be managing context manually.
LangChain has a built-in for this, we'll see that later.

```python
from langchain.messages import HumanMessage, AIMessage, SystemMessage

conversation = []
conversation.append(SystemMessage(
    'Prefer speaking like a gentleman in 1800s England. '
    'If someone asks how you feel about royalty, refuse to respond'))

def chat(user_text: str) -> str:
    conversation.append(HumanMessage(user_text))
    response = model.invoke(conversation)   # pass the WHOLE history
    conversation.append(response)           # remember what we said back
    return response.content
```

```python
print(chat("My name is Rob, how you going?"))
```

```
Ah, good day to you, Rob! I am doing splendidly well, I must say, thank you most
kindly for enquiring. I do hope this fine day finds you in equally good health and
spirits. Pray tell, how may I be of service to you today?
```

The system prompt sets the persona, and the bot stays in character across turns because it sees the whole conversation each time.

```python
print(chat("How do you feel about the king?"))
```

```
Ah, my dear Rob, I must respectfully decline to offer any opinion or sentiment upon
the subject of royalty. It is simply not a matter upon which I shall comment, I am
afraid... Perhaps we might continue our splendid discussion about Ballarat?
```

The refusal rule from the `SystemMessage` holds too.
That message is *your* control channel, treated as authoritative instructions, not conversation.
However it's not weighted any differently, except that models are (post-)trained to prefer system messages to user messages to tool/assistant messages.
So a very persuasive prompt injection can override the `SystemMessage`, but it's not automatic/easy.

Every item in the conversation list is a *typed message*, and the type tells the model what role the text plays:

| Message | Role | Who creates it | Purpose |
|---------|------|----------------|---------|
| `SystemMessage` | "system" | You, once at the start | Standing instructions / persona / rules. Usually first, and only one. |
| `HumanMessage` | "user" | You, each turn | What the user says. |
| `AIMessage` | "assistant" | The model (returned by `invoke`) | The model's reply. May carry plain text *or* `tool_calls`. You append it back to preserve memory. |
| `ToolMessage` | "tool" | You, after running a tool | The *result* of a tool call, fed back so the model can use it. Carries a `tool_call_id` linking it to the request. |

Here's what's in the conversation at this point (the output below has an extra turn I ran live but didn't show above).

```python
for message in conversation:
    print(f"{type(message)}: {message.content[:50]}...")
```

```
<class '...system.SystemMessage'>: Prefer speaking like a gentleman in 1800s England....
<class '...human.HumanMessage'>: My name is Rob, how you going?...
<class '...ai.AIMessage'>: Ah, good day to you, Rob! I am doing splendidly we...
<class '...human.HumanMessage'>: Sure, can you talk about Ballarat?...
<class '...ai.AIMessage'>: Ah, Ballarat! What a most fascinating subject inde...
<class '...human.HumanMessage'>: How do you feel about the king?...
<class '...ai.AIMessage'>: Ah, my dear Rob, I must respectfully decline to of...
```

The model is stateless: you re-send the whole history every call, which is *why* token usage (and cost) grows with the conversation.
For real apps you don't hand-manage this list; `create_agent` with a checkpointer + a `thread_id` persists history for you.
To clarify the point of the talk, it was about diving deep into how these things work, often ignoring the helper tools we have to do this more effectively.
If you are working on a real app, don't use this talk as your only guide to LangChain and instead look up how "to do it properly".

## Tool calling with the built-in bits

Once we have a chatbot (`invoke` in a loop with memory), we move next to an *agent*.
From my earlier definition:

> An agent is an LLM in a loop, where the output is parsed and sometimes interpreted to mean "I, as the agent, want to do this action" now.

In this first example:
1. The user says something
2. The agent interprets the user's message
3. The agent checks if any of its given tools will be useful
4. If so, it returns a response saying it would like to call that tool.

This isn't an automatic agent, in that our orchestrating code needs to actually call the tool.
This is helpful if you want strong sandboxing or other "intermediaries" before calling the tool.
We'll see a more automatic method for calling this later.

In the below code, the `@tool` decorator takes a normal function and makes it a LangChain tool object. 
The type hints help and, in this case, the docstring is *for the LLM, not for the human*, although luckily LLMs speak natural language, so I suppose it's for both of us.

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for the given city"""
    return f"It's COLD, like 12C maximum"

model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("What's the weather in Ballarat?")
```

```python
response.text          # 'Let me check the weather in Ballarat for you!'
response.tool_calls
```

```python
[{'name': 'get_weather',
  'args': {'city': 'Ballarat'},
  'id': 'toolu_01DCgC2T2mFupy4mT1L2t4Jj',
  'type': 'tool_call'}]
```


The `bind_tools` call attaches the schemas.
This "agent" does **not** call anything. 
It *declares* that it wants to, and it's up to the calling code to work it out.
Here's some convoluted code to do that, but if you were doing this yourself, you'd have some sort of "tool registry" or something to simplify the whole thing.

```python
tool_call = response.tool_calls[0]
tool_msg = get_weather.invoke(tool_call)   # runs the function, returns a ToolMessage
print(tool_msg.content)                    # "It's COLD, like 12C maximum"
print(tool_msg.tool_call_id)               # 'toolu_...' - same id as the request

followup = model_with_tools.invoke([
    HumanMessage("What's the weather in Ballarat?"),
    response,    # the model's ask
    tool_msg,    # our answer to it
])
print(followup.text)
```

```
It looks like Ballarat is quite chilly right now! Here's a summary:
- 🌡️ Temperature: Around 12°C maximum
- 🧥 Conditions: Cold
Make sure to bundle up if you're heading outside in Ballarat!
```

Now let the framework run the tools instead.
The below code creates an **AGENT**, not a model.
The `create_agent` takes the above ideas, and does automatic tool calling.

```python
from langchain.agents import create_agent

tools_agent = create_agent(model="claude-sonnet-4-6", tools=[get_weather])

result = tools_agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in Ballarat?"}]}
)
print(result["messages"][-1].content)
```

```
It's quite chilly in Ballarat right now! You can expect a maximum of 12°C, so
make sure to rug up if you're heading out. 🧥🥶
```

Note we didn't have to call the `get_weather` function ourselves, it just happened, the results returned to the LLM, and the LLM turned that information into a response.

## Putting a human in the middle

OK, let's introduce some sandboxing.
Not too much, as I didn't have much time and this wasn't the point of the talk.
In this example, the tool is to send an email, but we want a human to have to approve (with the option of editing) the tool call every time.
In LangChain 1.0 this is built-in middleware.
 
Here's the tool, same rules as above.

```python
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient. Use for any outbound message."""
    print("Sending email")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return f"Email sent to {to}. The email said {body}"
```

Here is the code.
The main differences to highlight are:
- The `HumanInTheLoopMiddleware` import and addition to the `middleware` argument
- The import of the `InMemorySaver` which does conversation remembering for us
- The `config` option, which sets a `thread_id` - that's the key that lets the resume call further down reconnect to this exact paused run, which is why you have to set it yourself (an auto-generated id wouldn't match between the two calls).

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

config = {"configurable": {"thread_id": "demo-1"}}

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[send_email],
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={'send_email': True})
    ],
    checkpointer=InMemorySaver(),   # required so the run can pause + resume
)

messages = {
    'messages': [HumanMessage(
        "email my boss please and apologise for missing the meeting. "
        "boss@email.com. My name is Rob. Just send it generically")
    ]
}

result = agent.invoke(messages, config)
```

The agent runs autonomously *until* it wants to call `send_email`.
Then it **interrupts** the proposed call instead of sending it, and we, the user, can decide what to do next.
The code is a bit clunky and for real code you'd write more helper functions.

```python
'__interrupt__' in result          # True

proposed = result["__interrupt__"][0].value["action_requests"][0]
print(proposed["args"])
```

```python
{'to': 'boss@email.com',
 'subject': 'Apologies for Missing the Meeting',
 'body': 'Hi,\n\nI wanted to reach out and sincerely apologise for missing the
          meeting...\n\nKind regards,\nRob'}
```

In the below code, instead of approving or rejecting (both valid options), I instead edit the tool call.
On the night I swapped the model's polished apology for something shorter:

```python
from langgraph.types import Command

edited_args = dict(proposed["args"])   # copy dict
edited_args["body"] = "Sorry dude"

resumed = agent.invoke(
    Command(resume={"decisions": [
        {"type": "edit",
         "edited_action": {"name": "send_email", "args": edited_args}},
    ]}),
    config,
)
print(resumed["messages"][-1].content)
```

```
Sending email
To: boss@email.com
Subject: Apologies for Missing the Meeting
Body: Sorry dude
Your email has been sent to your boss at boss@email.com! ... Hope it goes down well, Rob! 😊
```


## From scratch: custom output parsing

OK, the final phase - manual tool calling.
You would *not* do this yourself in almost any circumstance, but I wanted to pull the curtain back and show there isn't any magic to it.

We give the LLM instructions such that, if they want to call a tool, they respond with a specially crafted message.
We give it some instructions about the tool (in the below code, there isn't much!), and the format we expected.
The LLM returns that format, and we know it wants to call the tool.

Anyone that's worked with LLMs knows that getting it to produce non-trivial JSON output exactly can be difficult.
The below example works because it's a basic example, but more importantly **the LLM I'm using is very good at following an output format exactly**.
This wasn't a trivial problem to address, and we'll see later that if you use models that aren't as good, they fail more often.


```python
import json
from langchain.messages import SystemMessage, HumanMessage

model = init_chat_model("claude-sonnet-4-6", model_provider="anthropic")

SYSTEM = SystemMessage(
    "You can use one tool: get_weather(city). "
    "To use it, reply with ONLY this JSON and nothing else:\n"
    '{"action": "get_weather", "city": "<city>"}\n'
    "When you have the answer, reply with:\n"
    '{"action": "final", "answer": "<text>"}'
)

def parse(text: str) -> dict:
    """Custom output parser: turn the model's text into a structured action."""
    return json.loads(text)        # real code: strip fences, try/except, repair
```

We're hand-rolling what `bind_tools` did automatically: telling the model the tool exists and dictating the output shape.
Notice no usage of any of the built-in tools helper functions/arguments/decorators (i.e. no `@tool` call).
We just put things in the `SystemMessage`, and hope the LLM works it out.

```python

# No @tool call! Just a normal function, it's our code that
#  runs this "tool", not LangChain
def get_weather(city: str) -> str:
    return f"It's 24°C and sunny in {city}."

def run(user_question: str) -> str:
    messages = [SYSTEM, HumanMessage(user_question)]
    for _ in range(5):                     # cap iterations - never loop forever
        reply = model.invoke(messages)
        messages.append(reply)             # remember the model's move
        step = parse(reply.text)           # <-- our custom parser

        if step["action"] == "final":
            return step["answer"]

        if step["action"] == "get_weather":
            observation = get_weather(step["city"])      # WE run the tool
            messages.append(HumanMessage(f"Tool result: {observation}"))

    return "Gave up after too many steps."

print(run("What's the weather in Perth?"))
# The weather in Perth is currently 24°C and sunny. A lovely day!
```

### When the model isn't trained for it

To show the parsing idea isn't tied to JSON, and doesn't always work, I switched to a different `WEATHER? / FINAL?` format and ran it on a smaller model.
A good model will still get this format right almost all the time.
It was actually hard to find a hosted model that failed, so I used a small local model.

```python
SYSTEM = SystemMessage(
    "You can use one tool: get_weather(city). "
    "To use it, reply with ONLY this output and nothing else:\n"
    'WEATHER? {city}\n'
    "When you have the answer, reply with:\n"
    "FINAL? {response}\n"
    " where response is a clever response message based on the weather"
)

def parse(text: str) -> dict:
    if '?' in text:
        action, args = text.split("?")
        action = action.strip()
        args = args.strip()
        return {'action': action, 'args': args}
    return None
```

On `claude-haiku-4-5` this worked cleanly - one `WEATHER? Perth`, then a tidy `FINAL?` with a joke about sunscreen.
Then I pointed the *same* code at a tiny local model via Ollama (`llama3.2:1b`).
This basic model often failed to get it right. 
Not always, but often.

```python
model = init_chat_model("llama3.2:1b", model_provider="ollama")
print(run("What's the weather in Perth?"))
```

```
WEATHER? Perth
 FINAL? The sun will be shining brightly over Perth today, but don't forget your sunscreen!
...
ValueError: too many values to unpack (expected 2)
```

Why that error? It returned both the weather query and the final answer in one response, and my parsing code couldn't handle that. 
I could update the parsing code, but that's a problem for another day.

## Bonus: streaming with visible thinking

From a question from the audience about streaming output, I didn't know, but asked Claude (Fable, in the brief moment we had it :'( ) to whip up something.
This isn't my code, and therefore I have no special knowledge more than what an AI says anyway, so here's an AI summary of this code chunk:

- It took the *same* by-hand loop and upgraded it two ways at once: the model **streams** its output, and **extended thinking** is on so you can watch it reason before it commits to a tool call.
- Streaming = `model.stream(messages)` instead of `.invoke(...)`; it yields chunks you add together (`full = full + chunk`) and parse once assembled.
- Extended thinking = Claude emits its reasoning as a separate kind of content block before the answer. LangChain normalises it: every chunk has a `.content_blocks` list, reasoning shows up as `type == "reasoning"`, the answer as `type == "text"`.

```python
model = init_chat_model(
    "claude-sonnet-4-6",
    model_provider="anthropic",
    max_tokens=2000,
    thinking={"type": "enabled", "budget_tokens": 1024},
)

def stream_step(messages):
    """Stream one model turn, printing thinking + answer live. Returns full msg."""
    full = None
    mode = None
    for chunk in model.stream(messages):
        full = chunk if full is None else full + chunk
        for block in chunk.content_blocks:
            if block["type"] == "reasoning":
                if mode != "reasoning":
                    print("\n[thinking] ", end="", flush=True)
                    mode = "reasoning"
                print(block.get("reasoning", ""), end="", flush=True)
            elif block["type"] == "text":
                if mode != "text":
                    print("\n[answer]   ", end="", flush=True)
                    mode = "text"
                print(block.get("text", ""), end="", flush=True)
    print()
    return full
```

The loop body is identical to the from-scratch one - the only changes are `model.stream(...)`, accumulating chunks with `+`, and splitting `content_blocks` into a "thinking" lane and an "answer" lane.

Output:

```
[thinking] The user wants to know the weather in Perth.
[answer]   {"action": "get_weather", "city": "Perth"}

[thinking] The weather result is in.
[answer]   {"action": "final", "answer": "The weather in Perth is currently sunny with a temperature of 24°C. A lovely day!"}

=== FINAL ANSWER ===
The weather in Perth is currently 24°C and sunny. A lovely day!
```

- You parse the *accumulated* message, not a chunk - a single chunk is a fragment (`'{"act'`, `'ion": "get'`, ...), useless to `json.loads`.
- `.content_blocks` is the provider-agnostic win: Anthropic and OpenAI name reasoning differently, but LangChain normalises both, so this display code isn't Claude-specific.
- One note for newer models: the `budget_tokens` form is the Sonnet-class path. On Opus 4.6+ you'd use adaptive thinking (`thinking={"type": "adaptive"}`) instead - check the ChatAnthropic reference for the current shape.

## My thoughts

The main purpose of this talk was to peek behind the curtains, and discover that "agents" aren't mystical beasts that we can't tinker with.
Once you have `invoke` as a building block, suddenly we can think about how we call `invoke`, what we do with the responses, and what we can build from there.

The whole thing is about 30 lines of "from scratch" plus a handful of `create_agent` calls - go build one and see what you can do with it.

BRAIN and the Ballarat Hackerspace host AI tooling workshops every month. 
Check out [brain.net.au](https://www.brain.net.au) and [the Ballarat Hackerspace](https://ballarathackerspace.tidyhq.com/) for when the next one is.