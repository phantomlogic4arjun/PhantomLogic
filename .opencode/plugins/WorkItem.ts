


import { tool } from "@opencode-ai/plugin";

declare const Bun: {
  env: Record<string, string | undefined>;

  spawn(
    command: string[],
    options: {
      cwd: string;
      env: Record<string, string | undefined>;
      stdin: "pipe";
      stdout: "pipe";
      stderr: "pipe";
    },
  ): {
    stdin: {
      write(data: string): number;
      end(): void;
    };
    stdout: ReadableStream<Uint8Array>;
    stderr: ReadableStream<Uint8Array>;
    exited: Promise<number>;
  };
};

type PluginContext = {
  directory: string;
  worktree?: string;
};

export const WorkItemPlugin = async (
  pluginContext: PluginContext,
) => {
  const projectRoot =
    pluginContext.worktree ?? pluginContext.directory;

  return {
    tool: {
      work_item_create: tool({
        description:
          "Create Work Items through the Phantom Logic Work Item " +
          "Management interface. The calling agent identity is " +
          "verified by OpenCode and cannot be supplied by the caller. " +
          "After a successful operation, report the returned audit " +
          "events and operation outcome to the Orchestrator. The " +
          "Orchestrator is responsible for central audit submission.",

        args: {
          work_items: tool.schema.array(
            tool.schema.object({
              id: tool.schema.string(),
              title: tool.schema.string(),

              work_item_type: tool.schema.enum([
                "Epic",
                "Feature",
                "Use Case",
                "Requirement",
                "Change Request",
              ]),

              description: tool.schema.string().optional(),
              priority: tool.schema.string().optional(),
              build_number: tool.schema.string().optional(),

              acceptance_criteria: tool.schema
                .array(tool.schema.string())
                .optional(),

              relationships: tool.schema
                .array(
                  tool.schema.object({
                    target_id: tool.schema.string(),

                    relationship_type: tool.schema.enum([
                      "Parent Child",
                      "Affected Requirement",
                      "Violated Requirement",
                      "Failed Test Case",
                    ]),
                  }),
                )
                .optional(),
            }),
          ),
        },

        async execute(args, context) {
          const pythonProcess = Bun.spawn(
            [
              "python",
              "-m",
              "phantom_logic.work_items.interfaces.WorkItemAgentBridge",
            ],
            {
              cwd: projectRoot,

              env: {
                ...Bun.env,
                PHANTOM_LOGIC_CALLING_AGENT: context.agent,
              },

              stdin: "pipe",
              stdout: "pipe",
              stderr: "pipe",
            },
          );

          const stdoutPromise = new Response(
            pythonProcess.stdout,
          ).text();

          const stderrPromise = new Response(
            pythonProcess.stderr,
          ).text();

          pythonProcess.stdin.write(
            JSON.stringify({
              work_items: args.work_items,
            }),
          );

          pythonProcess.stdin.end();

          try {
            const exitCode = await pythonProcess.exited;

            const stdout = await stdoutPromise;
            const stderr = await stderrPromise;

            if (exitCode !== 0) {
              return {
                title: "Work Item Creation Failed",

                output: JSON.stringify({
                  success: false,
                  errors: [
                    stderr.trim() ||
                      `Python bridge exited with code ${exitCode}.`,
                  ],
                  work_items: [],
                  events: [],
                }),
              };
            }

            const result = JSON.parse(stdout);

            return {
              title: result.success
                ? "Work Item Creation Result"
                : "Work Item Creation Failed",

              output: JSON.stringify({
                ...result,

                audit_handoff_required: result.success,

                audit_handoff_instruction: result.success
                  ? "Report the operation outcome and all returned " +
                    "events to the Orchestrator for central auditing."
                  : null,
              }),
            };
          } catch (error) {
            return {
              title: "Work Item Creation Failed",

              output: JSON.stringify({
                success: false,

                errors: [
                  error instanceof Error
                    ? error.message
                    : "Unable to execute the Python Work Item bridge.",
                ],

                work_items: [],
                events: [],
              }),
            };
          }
        },
      }),
    },
  };
};
