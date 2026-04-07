# SBC-Chatbot

This project is a simple rule-based movie and series chatbot written in Python.  
It can:

- recommend movies or shows based on conditions such as genre, mood, language, director, or type
- answer basic information questions about titles in the database
- reply to simple greetings instead of always recommending something

## Run The Chatbot

From the project root, run:

```bash
python3 src/chatbot.py
```

To leave the chatbot, type:

```text
exit
```

## What The Chatbot Understands

The chatbot uses rules stored in [data/moviesseries.json].
Each rule has:

- `if`: the conditions of a movie or show
- `then`: the recommended title

The bot can use conditions like:

- type: `movie`, `series`
- director: for example `Christopher Nolan`
- language: `English`, `Korean`, `German`
- genre: `sci-fi`, `drama`, `comedy`, `thriller`, `fantasy`, `romance`, `horror`, `action`, `crime`, `animation`, `adventure`
- mood: `emotional`, `funny`, `light`, `dark`, `exciting`, `serious`, `scary`, `epic`
- duration: `short`, `medium`, `long`
- family-friendly requests like `family movie`
- year, when present in the request

When you ask for several conditions together, the bot only shows titles that match all of them.  
If nothing matches all the requested conditions, it tells you that directly.

## Example Prompts

Greetings:

```text
hello
hi
```

Recommendations:

```text
recommend me a sci-fi movie
recommend me a Korean movie
recommend me a Christopher Nolan movie
recommend me a dark thriller series
recommend me a short family movie
```

Multiple conditions:

```text
recommend me an emotional Korean sci-fi movie
recommend me a funny English series
recommend me a long serious movie
```

Information questions:

```text
tell me about Inception
give me information about Parasite
tell me about Dark
```

## Notes

- The chatbot is rule-based, so it only knows titles and conditions that exist in the JSON file.
- If a movie or series is not in the database, the chatbot cannot recommend it or provide information about it.
- Better recommendations depend on a better rule dataset. If you add more rules to the JSON file, the chatbot becomes more useful.
