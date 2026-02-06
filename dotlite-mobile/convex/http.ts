import {
  generateIcsCalendar,
  type IcsCalendar,
} from "ts-ics";
import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";

import { api } from "./_generated/api";
import { auth } from "./auth";
import { Id } from "./_generated/dataModel";

const http = httpRouter();

auth.addHttpRoutes(http);

http.route({
  path: "/ping",
  method: "GET",
  handler: httpAction(async () => {
    return new Response("pong", {
      status: 200,
      headers: {
        "Content-Type": "text/plain",
      },
    });
  }),
});

// /calendar/<userId> endpoint: generates ICS for user's tasks with due dates
http.route({
  path: "/calendar",
  method: "GET",
  handler: httpAction(async (ctx, req) => {
    const userId = req.url.split("?")[1];
    console.log(userId);
    // Get all lists for the user
    const lists = await ctx.runQuery(api.lists.getLists, {
      userId: userId as Id<"users">,
    });
    const userLists = lists.filter((list) => list.userId === userId);

    let allNodes: any[] = [];
    for (const list of userLists) {
      const nodes = await ctx.runQuery(api.lists.getNodes, {
        listId: list._id,
        userId: userId as Id<"users">,
      });
      allNodes = allNodes.concat(nodes);
    }

    // Only tasks with due dates
    const tasksWithDueDates = allNodes.filter(
      (node) => node.dueDate,
    );

    // Generate ICS events
    const events = tasksWithDueDates
      .map((node) => {
        const lines = node.text.split("\n");
        const title: string = lines[0];
        const description: string = lines.slice(1).join("\n");
        const dt = node.dueDate; // RFC 3339 string
        if (!dt) return null;

        // Normalize to UTC midnight and use VALUE=DATE
        const base = new Date(dt);
        const y = base.getUTCFullYear();
        const m = base.getUTCMonth();
        const d0 = base.getUTCDate();

        const date1 = new Date(Date.UTC(y, m, d0));
        const date2 = new Date(Date.UTC(y, m, d0 + 1)); // exclusive en

        return {
          summary: title,
          uid: node._id.toString(),
          description,
          start: { date: date1, type: "DATE" as "DATE" | undefined },
          end: { date: date2, type: "DATE" as "DATE" | undefined },
          timeTransparent: "TRANSPARENT" as "TRANSPARENT" | undefined,
          stamp: { date: new Date() },
        };
      })
      .filter((n) => n != null);

    const ics: IcsCalendar = {
      version: "2.0",
      prodId: "-//dotlist-lite//EN",
      name: "Dotlite Lite Tasks",
      events: events,
    };

    return new Response(generateIcsCalendar(ics), {
      status: 200,
      headers: {
        "Content-Type": "text; charset=utf-8",
        "Content-Disposition": `attachment; filename="tasks-${userId}.ics"`
      },
    });
  }),
});

export default http;
