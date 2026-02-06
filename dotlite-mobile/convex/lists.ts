import { v } from "convex/values";
import { query, mutation } from "./_generated/server";
import { getAuthUserId } from "@convex-dev/auth/server";

// Get all lists for the current user
export const getLists = query({
  args: {
    userId: v.optional(v.id("users")),
  },
  returns: v.array(
    v.object({
      _id: v.id("lists"),
      _creationTime: v.number(),
      name: v.string(),
      userId: v.id("users"),
      order: v.number(),
    })
  ),
  handler: async (ctx, args) => {
    let userId;
    if (args.userId) {
      userId = args.userId;
    } else {
      userId = await getAuthUserId(ctx);
      if (!userId) {
        throw new Error("Not authenticated");
      }
    }
    const lists = await ctx.db
      .query("lists")
      .withIndex("by_user_and_order", (q) => q.eq("userId", userId))
      .order("asc")
      .collect();

    return lists;
  },
});

// Get nodes for a specific list
export const getNodes = query({
  args: {
    userId: v.optional(v.id("users")),
    listId: v.id("lists"),
  },
  returns: v.array(
    v.object({
      _id: v.id("nodes"),
      _creationTime: v.number(),
      text: v.string(),
      state: v.union(v.literal("red"), v.literal("yellow"), v.literal("green")),
      listId: v.id("lists"),
      order: v.number(),
      dueDate: v.optional(v.string()),
    })
  ),
  handler: async (ctx, args) => {
    let userId;
    if (args.userId) {
      userId = args.userId;
    } else {
      userId = await getAuthUserId(ctx);
      if (!userId) {
        throw new Error("Not authenticated");
      }
    }
    if (!userId) {
      throw new Error("Not authenticated");
    }

    // Verify the list belongs to the user
    const list = await ctx.db.get(args.listId);
    if (!list || list.userId !== userId) {
      throw new Error("List not found or access denied");
    }

    const nodes = await ctx.db
      .query("nodes")
      .withIndex("by_list_and_order", (q) => q.eq("listId", args.listId))
      .order("asc")
      .collect();

    return nodes;
  },
});

// Create a new list
export const createList = mutation({
  args: {
    name: v.string(),
  },
  returns: v.id("lists"),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    // Get the current max order for this user's lists
    const existingLists = await ctx.db
      .query("lists")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();

    const maxOrder = existingLists.reduce((max, list) => Math.max(max, list.order), -1);

    const listId = await ctx.db.insert("lists", {
      name: args.name,
      userId,
      order: maxOrder + 1,
    });

    return listId;
  },
});

// Update list name
export const updateListName = mutation({
  args: {
    listId: v.id("lists"),
    name: v.string(),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const list = await ctx.db.get(args.listId);
    if (!list || list.userId !== userId) {
      throw new Error("List not found or access denied");
    }

    await ctx.db.patch(args.listId, { name: args.name });
    return null;
  },
});

// Delete a list and all its nodes
export const deleteList = mutation({
  args: {
    listId: v.id("lists"),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const list = await ctx.db.get(args.listId);
    if (!list || list.userId !== userId) {
      throw new Error("List not found or access denied");
    }

    // Delete all nodes in the list
    const nodes = await ctx.db
      .query("nodes")
      .withIndex("by_list", (q) => q.eq("listId", args.listId))
      .collect();

    for (const node of nodes) {
      await ctx.db.delete(node._id);
    }

    // Delete the list
    await ctx.db.delete(args.listId);
    return null;
  },
});

// Reorder lists
export const reorderLists = mutation({
  args: {
    listIds: v.array(v.id("lists")),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    // Verify all lists belong to the user
    for (const listId of args.listIds) {
      const list = await ctx.db.get(listId);
      if (!list || list.userId !== userId) {
        throw new Error("List not found or access denied");
      }
    }

    // Update order for each list
    for (let i = 0; i < args.listIds.length; i++) {
      await ctx.db.patch(args.listIds[i], { order: i });
    }

    return null;
  },
});

// Create a new node
export const createNode = mutation({
  args: {
    listId: v.id("lists"),
    text: v.string(),
    state: v.union(v.literal("red"), v.literal("yellow"), v.literal("green")),
    dueDate: v.optional(v.string()),
  },
  returns: v.id("nodes"),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const list = await ctx.db.get(args.listId);
    if (!list || list.userId !== userId) {
      throw new Error("List not found or access denied");
    }

    // Get the current max order for this list's nodes
    const existingNodes = await ctx.db
      .query("nodes")
      .withIndex("by_list", (q) => q.eq("listId", args.listId))
      .collect();

    const maxOrder = existingNodes.reduce((max, node) => Math.max(max, node.order), -1);

    const nodeId = await ctx.db.insert("nodes", {
      text: args.text,
      state: args.state,
      listId: args.listId,
      order: maxOrder + 1,
      dueDate: args.dueDate ?? undefined,
    });

    return nodeId;
  },
});

// Update node text
export const updateNodeText = mutation({
  args: {
    nodeId: v.id("nodes"),
    text: v.string(),
    dueDate: v.optional(v.string()),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const node = await ctx.db.get(args.nodeId);
    if (!node) {
      throw new Error("Node not found");
    }

    const list = await ctx.db.get(node.listId);
    if (!list || list.userId !== userId) {
      throw new Error("Access denied");
    }

    await ctx.db.patch(args.nodeId, { text: args.text, dueDate: args.dueDate ?? undefined });
    return null;
  },
});

// Update node state
export const updateNodeState = mutation({
  args: {
    nodeId: v.id("nodes"),
    state: v.union(v.literal("red"), v.literal("yellow"), v.literal("green")),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const node = await ctx.db.get(args.nodeId);
    if (!node) {
      throw new Error("Node not found");
    }

    const list = await ctx.db.get(node.listId);
    if (!list || list.userId !== userId) {
      throw new Error("Access denied");
    }

    await ctx.db.patch(args.nodeId, { state: args.state });
    return null;
  },
});

// Delete a node
export const deleteNode = mutation({
  args: {
    nodeId: v.id("nodes"),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    const node = await ctx.db.get(args.nodeId);
    if (!node) {
      throw new Error("Node not found");
    }

    const list = await ctx.db.get(node.listId);
    if (!list || list.userId !== userId) {
      throw new Error("Access denied");
    }

    await ctx.db.delete(args.nodeId);
    return null;
  },
});

// Initialize user with a default list
export const initializeUserLists = mutation({
  args: {},
  returns: v.id("lists"),
  handler: async (ctx) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) {
      throw new Error("Not authenticated");
    }

    // Check if user already has lists
    const existingLists = await ctx.db
      .query("lists")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();

    if (existingLists.length > 0) {
      return existingLists[0]._id;
    }

    // Create default list
    const listId = await ctx.db.insert("lists", {
      name: "My List",
      userId,
      order: 0,
    });

    // Create default nodes
    const defaultNodes = [
      { text: "Item 1", state: "red" as const },
      { text: "Item 2", state: "red" as const },
      { text: "Item 3", state: "red" as const },
    ];

    for (let i = 0; i < defaultNodes.length; i++) {
      await ctx.db.insert("nodes", {
        text: defaultNodes[i].text,
        state: defaultNodes[i].state,
        listId,
        order: i,
      });
    }

    return listId;
  },
});
