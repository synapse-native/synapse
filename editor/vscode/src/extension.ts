import * as path from "path";
import { ExtensionContext, window, workspace, commands } from "vscode";

import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

export function activate(context: ExtensionContext): void {
    const disposables = [
        commands.registerCommand("synapse.restartLsp", () => restartLsp(context)),
    ];

    startLsp(context);

    context.subscriptions.push(...disposables);
}

function startLsp(context: ExtensionContext): void {
    const config = workspace.getConfiguration("synapse.lsp");
    const command: string = config.get<string>("path", "synapse");
    let args: string[] = config.get<string[]>("args", ["--lsp"]);

    const serverOptions: ServerOptions = {
        run: {
            command,
            args,
            transport: TransportKind.stdio,
        },
        debug: {
            command,
            args: [...args, "--debug"],
            transport: TransportKind.stdio,
        },
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: "file", language: "synapse" },
        ],
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher("**/*.syn"),
        },
        outputChannelName: "Synapse LSP",
        traceOutputChannel: window.createOutputChannel("Synapse LSP Trace"),
    };

    client = new LanguageClient(
        "synapse-lsp",
        "Synapse Language Server",
        serverOptions,
        clientOptions,
    );

    client.registerProposedFeatures();

    client.start();
}

function restartLsp(context: ExtensionContext): void {
    if (client) {
        client.stop().then(() => {
            client = undefined;
            startLsp(context);
        });
    } else {
        startLsp(context);
    }
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}