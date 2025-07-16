import { eq } from "drizzle-orm";
import { poolCreated } from "./db/schema/Listener"; // Adjust the import path as necessary
import { types,db,App } from "sim-idx"; // Import schema to ensure it's registered

const filterToken0 = types.Address.from("7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9");

const app = App.create()
app.get("/*", async (c) => {
  try {
    const result = await db.client(c).select().from(poolCreated).where(
      eq(poolCreated.token0, filterToken0)
    ).limit(5);

    return Response.json({
      result: result,
    });
  } catch (e) {
    console.error("Database operation failed:", e);
    return Response.json({ error: (e as Error).message }, { status: 500 });
  }
});

export default app;
