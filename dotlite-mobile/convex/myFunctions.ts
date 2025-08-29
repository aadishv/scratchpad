import { query } from "./_generated/server";
// import { api } from "./_generated/api";
import { getAuthUserId } from "@convex-dev/auth/server";

export const getUser = query({
  args: {},
  handler: async (ctx, _) => {
    const userId = await getAuthUserId(ctx);
    const user = userId === null ? null : await ctx.db.get(userId);
    return {
      viewer: user?.name ?? null,
      image: user?.image ?? null,
      id: userId ?? null,
    };
  },
});
