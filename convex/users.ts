import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const getUserSettings = query({
    handler: async (ctx) => {
        const identity = await ctx.auth.getUserIdentity();
        if (!identity) {
            return null;
        }

        const user = await ctx.db
            .query("users")
            .withIndex("by_tokenIdentifier", (q) => q.eq("tokenIdentifier", identity.tokenIdentifier))
            .unique();

        return user;
    },
});

export const updateUserSettings = mutation({
    args: {
        headerFont: v.optional(v.string()),
        bodyFont: v.optional(v.string()),
        theme: v.optional(v.string()),
        randomnessTemperature: v.optional(v.number()),
    },
    handler: async (ctx, args) => {
        const identity = await ctx.auth.getUserIdentity();
        if (!identity) {
            throw new Error("You must be logged in to update settings.");
        }

        const user = await ctx.db
            .query("users")
            .withIndex("by_tokenIdentifier", (q) => q.eq("tokenIdentifier", identity.tokenIdentifier))
            .unique();

        if (!user) {
            throw new Error("User not found.");
        }

        await ctx.db.patch(user._id, args);
    },
});
