import { internalAction, internalMutation, mutation, query } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

// All of this is being done in an internal action because it's not something that should be exposed to the public
// and we are calling a third party API.
export const fetchAndProcessPosts = internalAction({
    args: {
        temperature: v.optional(v.number()),
    },
    handler: async (ctx, { temperature }) => {
        const response = await fetch("http://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=300");
        if (!response.ok) {
            throw new Error(`Failed to fetch posts from Hacker News: ${response.statusText}`);
        }
        const data = await response.json();

        let posts = data.hits.filter((post: any) => post.url);

        // Sort by upvotes + randomness
        const temp = temperature ?? 1.0;
        posts.sort((a: any, b: any) => {
            const aScore = a.points + Math.random() * temp;
            const bScore = b.points + Math.random() * temp;
            return bScore - aScore;
        });

        // We are going to clear all the old posts and insert the new ones.
        // This is not the most efficient way to do this, but it's the simplest for now.
        await ctx.runMutation(internal.hackerNews.clearAndInsertPosts, {
            posts: posts.map((post: any) => ({
                title: post.title,
                url: post.url,
                author: post.author,
                points: post.points,
                num_comments: post.num_comments,
                objectID: post.objectID,
                hnId: parseInt(post.objectID),
            })),
        });
    },
});

export const clearAndInsertPosts = internalMutation({
    args: {
        posts: v.array(
            v.object({
                title: v.string(),
                url: v.string(),
                author: v.string(),
                points: v.number(),
                num_comments: v.number(),
                objectID: v.string(),
                hnId: v.number(),
            })
        ),
    },
    handler: async (ctx, { posts }) => {
        // A more efficient way to do this would be to check for existing posts
        // and only insert new ones, but for the prototype, this is fine.
        const existingPosts = await ctx.db.query("posts").collect();
        for (const post of existingPosts) {
            await ctx.db.delete(post._id);
        }

        for (const post of posts) {
            await ctx.db.insert("posts", post);
        }
    },
});

// A public mutation to trigger the process
export const triggerFetchAndProcessPosts = mutation({
    args: {
        temperature: v.optional(v.number()),
    },
    handler: async (ctx, { temperature }) => {
        await ctx.scheduler.runAfter(0, internal.hackerNews.fetchAndProcessPosts, { temperature });
    },
});

export const getPosts = query({
    handler: async (ctx) => {
        const identity = await ctx.auth.getUserIdentity();
        if (!identity) {
            // Not logged in, show all posts
            return await ctx.db.query("posts").collect();
        }

        const user = await ctx.db
            .query("users")
            .withIndex("by_tokenIdentifier", (q) => q.eq("tokenIdentifier", identity.tokenIdentifier))
            .unique();

        if (!user || !user.seenPosts) {
            return await ctx.db.query("posts").collect();
        }

        const allPosts = await ctx.db.query("posts").collect();
        const seenPostIds = new Set(user.seenPosts.map((id) => id.toString()));

        return allPosts.filter((post) => !seenPostIds.has(post._id.toString()));
    }
});

import { Readability } from "@mozilla/readability";
import { JSDOM } from "jsdom";

export const extractContent = internalAction({
    args: {
        postId: v.id("posts"),
        url: v.string(),
    },
    handler: async (ctx, { postId, url }) => {
        try {
            const response = await fetch(url);
            const html = await response.text();
            const doc = new JSDOM(html, {
                url: url,
            });
            const reader = new Readability(doc.window.document);
            const article = reader.parse();

            if (article) {
                await ctx.runMutation(internal.hackerNews.updatePostContent, {
                    postId,
                    content: article.content,
                });
            }
        } catch (e) {
            console.error(`Failed to extract content from ${url}`, e);
            // We can choose to do something else here, like mark the post as failed to extract
        }
    },
});

export const updatePostContent = internalMutation({
    args: {
        postId: v.id("posts"),
        content: v.string(),
    },
    handler: async (ctx, { postId, content }) => {
        await ctx.db.patch(postId, { content });
    },
});

export const triggerExtractContent = mutation({
    args: {
        postId: v.id("posts"),
        url: v.string(),
    },
    handler: async (ctx, { postId, url }) => {
        await ctx.scheduler.runAfter(0, internal.hackerNews.extractContent, { postId, url });
    },
});
