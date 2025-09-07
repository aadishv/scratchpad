import { action, query } from "./_generated/server";
import { v } from "convex/values";

export const getComments = action({
    args: {
        hnId: v.number(),
    },
    handler: async (ctx, { hnId }) => {
        const response = await fetch(`http://hn.algolia.com/api/v1/items/${hnId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch comments from Hacker News: ${response.statusText}`);
        }
        const data = await response.json();
        return data.children;
    },
});
