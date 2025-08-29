# ![Dotlist Lite](public/favicon.png) Dotlist Lite

[Dotlist](https://dotlist.edwrdq.xyz/) is a popular open-source task management app. It's currently maintained by edwrdq; I (aadishv) am a contributor to the project. I wrote out much of the core UI code which the app lives on today.

Dotlist Lite (this repo) is a lightweight version of Dotlist, designed to be fast and efficient, with a focus on simplicity and ease of use. It has the same core idea as Dotlist -- lists of items with a red/yellow/green status -- and the same tech stack and interactions, but guts Dotlist of its more complex features.

By using Dotlist Lite, you trade away these features for a much nicer and more polished UX. Because there are less features overall, I spent a lot of time optimizing micro-interactions and the overall feel of the app to make sure it feels snappy, responsive, fluid, clean, and elegant.

Here is a general map of what you should do if you want certain features:

* Team features (notifications, team lists, comments): Use Dotlist. Their Teams implementation is not super pretty but it works.
* AI features: You probably don't need them? and if you do, use Dotlist. They do have AI features (albeit not super useful ones).
* Subtasks: Dotlist Lite supports multiple lines -- have one line for each subtask and use asterisks (*) to organize. If you want proper subtasks (which you quite certainly don't really need), either use mutliple lists or switch to Dotlist.
* Everything else: Dotlist Lite has it :D In fact, Dotlist Lite often gets features first before I upstream them into Dotlist -- such as calendar integration.

Check it out at [dotlist-lite.vercel.app](https://dotlist-lite.vercel.app).
