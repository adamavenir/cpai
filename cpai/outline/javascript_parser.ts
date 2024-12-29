import * as ts from 'typescript';
import { readFileSync } from 'fs';

interface FunctionInfo {
    name: string;
    line: number;
    parameters: string;
    returnType?: string;
    isAsync: boolean;
    isExport: boolean;
    isDefaultExport: boolean;
    leadingComment?: string;
    nodeType: string;
}

function getLeadingComment(node: ts.Node, sourceFile: ts.SourceFile): string | undefined {
    const fullText = sourceFile.getFullText();
    const nodeStart = node.getFullStart();
    const commentRanges = ts.getLeadingCommentRanges(fullText, nodeStart);
    
    if (!commentRanges || commentRanges.length === 0) {
        return undefined;
    }

    return commentRanges
        .map(range => fullText.slice(range.pos, range.end))
        .join('\n');
}

function getParameters(node: ts.Node): string {
    if (ts.isFunctionLike(node)) {
        return node.parameters
            .map(p => p.getText())
            .join(', ');
    }
    return '';
}

function getReturnType(node: ts.Node, sourceFile: ts.SourceFile): string | undefined {
    if (ts.isFunctionLike(node)) {
        if (node.type) {
            return node.type.getText(sourceFile);
        }
        // For React components, check for JSX return type
        if (ts.isSourceFile(node.parent) || ts.isModuleBlock(node.parent)) {
            const body = ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) 
                ? node.body 
                : ts.isArrowFunction(node) ? node.body : undefined;
            
            if (body && ts.isBlock(body)) {
                const returnStatements = findReturnStatements(body);
                for (const ret of returnStatements) {
                    if (ret.expression && ts.isJsxElement(ret.expression) || ts.isJsxFragment(ret.expression)) {
                        return 'JSX.Element';
                    }
                }
            } else if (body && (ts.isJsxElement(body) || ts.isJsxFragment(body))) {
                return 'JSX.Element';
            }
        }
    }
    return undefined;
}

function findReturnStatements(node: ts.Node): ts.ReturnStatement[] {
    const returns: ts.ReturnStatement[] = [];
    
    function visit(node: ts.Node) {
        if (ts.isReturnStatement(node)) {
            returns.push(node);
        }
        ts.forEachChild(node, visit);
    }
    
    visit(node);
    return returns;
}

function getExportType(node: ts.Node): 'default' | 'named' | null {
    // Check if node has modifiers property and it's an array
    if (!('modifiers' in node) || !Array.isArray((node as any).modifiers)) {
        return null;
    }

    const modifiers = (node as any).modifiers as ts.ModifierLike[];
    const hasExport = modifiers.some(m => m.kind === ts.SyntaxKind.ExportKeyword);
    const hasDefault = modifiers.some(m => m.kind === ts.SyntaxKind.DefaultKeyword);

    if (hasExport && hasDefault) {
        return 'default';
    } else if (hasExport) {
        return 'named';
    }

    return null;
}

function extractFunctions(sourceFile: ts.SourceFile): FunctionInfo[] {
    const functions: FunctionInfo[] = [];

    function visit(node: ts.Node) {
        if (ts.isClassDeclaration(node)) {
            // Only visit class members, don't add the class itself
            node.members.forEach(member => {
                if (ts.isMethodDeclaration(member) || ts.isConstructorDeclaration(member)) {
                    const methodName = ts.isConstructorDeclaration(member) ? 'constructor' : member.name?.getText() || 'anonymous';
                    const exportType = getExportType(member);
                    functions.push({
                        name: methodName,
                        line: sourceFile.getLineAndCharacterOfPosition(member.getStart()).line + 1,
                        leadingComment: getLeadingComment(member, sourceFile),
                        parameters: getParameters(member),
                        isAsync: member.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword) || false,
                        isExport: exportType !== null,
                        isDefaultExport: exportType === 'default',
                        nodeType: 'method'
                    });
                }
            });
        } else if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
            let name = '';
            let isExport = false;
            let isDefaultExport = false;

            if (ts.isFunctionDeclaration(node)) {
                name = node.name?.text || 'anonymous';
                const exportType = getExportType(node);
                isExport = exportType !== null;
                isDefaultExport = exportType === 'default';
            } else if (ts.isVariableDeclaration(node.parent)) {
                name = node.parent.name.getText();
                // Check for export on variable declaration
                const statement = node.parent.parent?.parent;
                if (ts.isVariableStatement(statement)) {
                    const exportType = getExportType(statement);
                    isExport = exportType !== null;
                    isDefaultExport = exportType === 'default';
                }
                // Check for separate export default
                if (!isExport) {
                    ts.forEachChild(sourceFile, child => {
                        if (ts.isExportAssignment(child) && 
                            ts.isIdentifier(child.expression) && 
                            child.expression.text === name) {
                            isExport = true;
                            isDefaultExport = true;
                        }
                    });
                }
            }

            if (name) {
                functions.push({
                    name,
                    line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
                    leadingComment: getLeadingComment(node, sourceFile),
                    parameters: getParameters(node),
                    isAsync: node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword) || false,
                    isExport,
                    isDefaultExport,
                    nodeType: 'function'
                });
            }
        }

        ts.forEachChild(node, visit);
    }

    visit(sourceFile);
    return functions;
}

// Read input from stdin
let content = '';
process.stdin.on('data', chunk => {
    content += chunk;
});

process.stdin.on('end', () => {
    try {
        const sourceFile = ts.createSourceFile(
            'temp.ts',
            content,
            ts.ScriptTarget.Latest,
            true,
            ts.ScriptKind.TSX
        );
        
        const functions = extractFunctions(sourceFile);
        console.log(JSON.stringify(functions));
    } catch (error) {
        console.error(`Failed to parse source: ${error}`);
        process.exit(1);
    }
});
