import assert from "node:assert/strict";
import { WorkItemPlugin } from "../../.opencode/plugins/WorkItem.ts";

const plugin = await WorkItemPlugin({
  directory: process.cwd(),
});

assert.ok(plugin);
assert.ok(plugin.tool);
assert.ok(
  Object.hasOwn(plugin.tool, "work_item_create"),
  "Work Item plugin must register work_item_create.",
);

console.log("Work Item plugin initialization successful.");
console.log("Registered tools:", Object.keys(plugin.tool).join(", "));
