import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";
import { authTables } from "@convex-dev/auth/server";

// The schema is normally optional, but Convex Auth
// requires indexes defined on `authTables`.
// The schema provides more precise TypeScript types.
export default defineSchema({
  ...authTables,
  lists: defineTable({
    name: v.string(),
    userId: v.id("users"),
    order: v.number(),
  })
    .index("by_user", ["userId"])
    .index("by_user_and_order", ["userId", "order"]),
  nodes: defineTable({
    text: v.string(),
    state: v.union(v.literal("red"), v.literal("yellow"), v.literal("green")),
    listId: v.id("lists"),
    order: v.number(),
    dueDate: v.optional(v.string()), // RFC 3339 date string or null
  })
    .index("by_list", ["listId"])
    .index("by_list_and_order", ["listId", "order"]),
});
