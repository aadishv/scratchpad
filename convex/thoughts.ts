import { mutation } from "./_generated/server";
import { v } from "convex/values";
import { query } from "./_generated/server";
import { api } from "./_generated/api";

export const saveThought = mutation({
    args: {
        postId: v.id("posts"),
        text: v.string(),
    },
    handler: async (ctx, { postId, text }) => {
        const identity = await ctx.auth.getUserIdentity();
        if (!identity) {
            throw new Error("You must be logged in to save a thought.");
        }

        const user = await ctx.db
            .query("users")
            .withIndex("by_tokenIdentifier", (q) => q.eq("tokenIdentifier", identity.tokenIdentifier))
            .unique();

        if (!user) {
            throw new Error("User not found.");
        }

        await ctx.db.insert("thoughts", {
            userId: user._id,
            postId,
            text,
        });

        const seenPosts = user.seenPosts ?? [];
        await ctx.db.patch(user._id, {
            seenPosts: [...seenPosts, postId],
        });
    },
});

export const getThoughtsForPost = query({
    args: {
        postId: v.id("posts"),
    },
    handler: async (ctx, { postId }) => {
        const identity = await ctx.auth.getUserIdentity();
        if (!identity) {
            // Not logged in, no thoughts
            return [];
        }

        return await ctx.db
            .query("thoughts")
            .withIndex("by_user_post", (q) => q.eq("userId", identity.subject).eq("postId", postId))
            .collect();
    },
});
