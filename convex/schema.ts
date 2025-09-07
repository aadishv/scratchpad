import { defineSchema, defineTable } from "convex/server";
import { authTables } from "@convex-dev/auth/server";
import { v } from "convex/values";

export default defineSchema({
  ...authTables,
  posts: defineTable({
    title: v.string(),
    url: v.string(),
    author: v.string(),
    points: v.number(),
    num_comments: v.number(),
    objectID: v.string(),
    content: v.optional(v.string()),
    hnId: v.number(),
  }).index("by_objectID", ["objectID"]),

  thoughts: defineTable({
    userId: v.id("users"),
    postId: v.id("posts"),
    text: v.string(),
  }).index("by_user_post", ["userId", "postId"]),

  // This table is managed by Convex Auth, but we can add fields to it
  users: defineTable({
    // ...fields from authTables
    seenPosts: v.optional(v.array(v.id("posts"))),
    // other settings
    headerFont: v.optional(v.string()),
    bodyFont: v.optional(v.string()),
    theme: v.optional(v.string()),
    randomnessTemperature: v.optional(v.number()),

    // from auth
    name: v.optional(v.string()),
    email: v.optional(v.string()),
    pictureUrl: v.optional(v.string()),
  }).index("by_email", ["email"]),
});
