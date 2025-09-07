# Aadish's template

What I use for building most of my web apps nowadays.

## Key technologies

* **Convex** for the backend. It's truly magical.
* **React + Vite** for the frontend. Very simple and avoids bloat. Also easy to deploy.
* **Tailwind + shadcn** for styling. Super fast to build UIs.
* **Convex Auth set up** -- integrates beautifully with Convex and has great docs.
* **Wouter** for routing. Very lightweight; React Router is probably also in a good place now, but I haven't tried it yet.

## Other recommended libraries

* lucide-react for icons.
* react-query for data fetching and caching. (This won't be needed since Convex handles data fetching and caching for you, but it's helpful for calling 3rd party APIs and such.)
* nuqs for handling query params. Remember, URLs are a great way to store state!
* Sonner for toasts.
* AI SDK for adding AI stuff.
* etc.

## Deployment

Vercel.

## But what if I want...

**RSCs?** This template isn't for you, then.

**Static content?** Check out Astro!

**Live update?** Convex does that automatically! Just part of the magic ✨

## Setup

I'll eventually write it out fully later, but the gist is:
1. Clone the repo.
2. Run `bun install` then `bun dev` to set up Convex.
3. Follow Convex Auth docs for setting up authentication env variables.
4. Try to deploy it and go through hell.
