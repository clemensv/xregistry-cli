// file: esbuild.js


const { build } = require("esbuild");
const { copy } = require("esbuild-plugin-copy");

const baseConfig = {
    bundle: true,
    minify: process.env.NODE_ENV === "production",
    sourcemap: process.env.NODE_ENV !== "production",
};

const extensionConfig = {
    ...baseConfig,
    platform: "node",
    format: "cjs",
    entryPoints: ["./src/extension.ts"],
    outfile: "./dist/extension.js",
    external: ["vscode"],
    plugins: [
        // copy schema file(s) from parent xregistry/schemas directory to out directory
        copy({
            resolveFrom: "cwd",
            assets: {
              from: ["../xregistry/schemas/*.json"],
              to: ["./schemas"],
            },
        }),
        // copy commands.json from parent xregistry directory to out directory
        copy({
            resolveFrom: "cwd",
            assets: {
              from: ["../xregistry/commands.json"],
              to: ["./dist"],
            },
        })
    ]
};

const watchConfig = {
    watch: {
        onRebuild(error, result) {
            console.log("[watch] build started");
            if (error) {
                error.errors.forEach(error =>
                    console.error(`> ${error.location.file}:${error.location.line}:${error.location.column}: error: ${error.text}`)
                );
            } else {
                console.log("[watch] build finished");
            }
        },
    },
};

const webviewConfig = {
    ...baseConfig,
    target: "es2020",
    format: "esm",
    entryPoints: ["./src/webview/main.ts"],
    outfile: "./out/webview.js",
    plugins: [
        // Copy webview css files to `out` directory unaltered
        copy({
          resolveFrom: "cwd",
          assets: {
            from: ["./src/webview/*.css"],
            to: ["./out"],
          },
        }),
        // Copy webview css files to `out` directory unaltered
        copy({
            resolveFrom: "cwd",
            assets: {
              from: ["./src/webview/*.ttf"],
              to: ["./out"],
            },
          })
    ],
};

(async () => {
    const args = process.argv.slice(2);
    try {
        if (args.includes("--watch")) {
            // Build and watch source code
            console.log("[watch] build started");
            await build({
                ...extensionConfig,
                ...watchConfig,
            });
            await build({
                ...webviewConfig,
                ...watchConfig,
              });
            console.log("[watch] build finished");
        } else {
            // Build source code
            await build(extensionConfig);
            await build(webviewConfig);
            console.log("build complete");
        }
    } catch (err) {
        process.stderr.write(err.stderr);
        process.exit(1);
    }
})();