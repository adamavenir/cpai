"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var ts = require("typescript");
function getLeadingComment(node, sourceFile) {
    var fullText = sourceFile.getFullText();
    var nodeStart = node.getFullStart();
    var commentRanges = ts.getLeadingCommentRanges(fullText, nodeStart);
    if (!commentRanges || commentRanges.length === 0) {
        return undefined;
    }
    return commentRanges
        .map(function (range) { return fullText.slice(range.pos, range.end); })
        .join('\n');
}
function getParameters(node) {
    if (ts.isFunctionLike(node)) {
        return node.parameters
            .map(function (p) { return p.getText(); })
            .join(', ');
    }
    return '';
}
function getReturnType(node, sourceFile) {
    if (ts.isFunctionLike(node)) {
        if (node.type) {
            return node.type.getText(sourceFile);
        }
        // For React components, check for JSX return type
        if (ts.isSourceFile(node.parent) || ts.isModuleBlock(node.parent)) {
            var body = ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)
                ? node.body
                : ts.isArrowFunction(node) ? node.body : undefined;
            if (body && ts.isBlock(body)) {
                var returnStatements = findReturnStatements(body);
                for (var _i = 0, returnStatements_1 = returnStatements; _i < returnStatements_1.length; _i++) {
                    var ret = returnStatements_1[_i];
                    if (ret.expression && ts.isJsxElement(ret.expression) || ts.isJsxFragment(ret.expression)) {
                        return 'JSX.Element';
                    }
                }
            }
            else if (body && (ts.isJsxElement(body) || ts.isJsxFragment(body))) {
                return 'JSX.Element';
            }
        }
    }
    return undefined;
}
function findReturnStatements(node) {
    var returns = [];
    function visit(node) {
        if (ts.isReturnStatement(node)) {
            returns.push(node);
        }
        ts.forEachChild(node, visit);
    }
    visit(node);
    return returns;
}
function getExportType(node) {
    // Check if node has modifiers property and it's an array
    if (!('modifiers' in node) || !Array.isArray(node.modifiers)) {
        return null;
    }
    var modifiers = node.modifiers;
    var hasExport = modifiers.some(function (m) { return m.kind === ts.SyntaxKind.ExportKeyword; });
    var hasDefault = modifiers.some(function (m) { return m.kind === ts.SyntaxKind.DefaultKeyword; });
    if (hasExport && hasDefault) {
        return 'default';
    }
    else if (hasExport) {
        return 'named';
    }
    return null;
}
function extractFunctions(sourceFile) {
    var functions = [];
    function visit(node) {
        var _a, _b, _c, _d;
        if (ts.isClassDeclaration(node)) {
            // Add the class itself
            var className_1 = ((_a = node.name) === null || _a === void 0 ? void 0 : _a.getText()) || 'anonymous';
            var exportType = getExportType(node);
            functions.push({
                name: className_1,
                line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
                leadingComment: getLeadingComment(node, sourceFile),
                parameters: '',
                isAsync: false,
                isExport: exportType !== null,
                isDefaultExport: exportType === 'default',
                nodeType: 'class'
            });
            // Visit class members
            node.members.forEach(function (member) {
                var _a, _b;
                if (ts.isMethodDeclaration(member) || ts.isConstructorDeclaration(member)) {
                    var methodName = ts.isConstructorDeclaration(member) ? 'constructor' : ((_a = member.name) === null || _a === void 0 ? void 0 : _a.getText()) || 'anonymous';
                    var exportType_1 = getExportType(member);
                    functions.push({
                        name: "".concat(className_1, ".").concat(methodName),
                        line: sourceFile.getLineAndCharacterOfPosition(member.getStart()).line + 1,
                        leadingComment: getLeadingComment(member, sourceFile),
                        parameters: getParameters(member),
                        isAsync: ((_b = member.modifiers) === null || _b === void 0 ? void 0 : _b.some(function (m) { return m.kind === ts.SyntaxKind.AsyncKeyword; })) || false,
                        isExport: exportType_1 !== null,
                        isDefaultExport: exportType_1 === 'default',
                        nodeType: 'method'
                    });
                }
            });
        }
        else if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
            var name_1 = '';
            var isExport_1 = false;
            var isDefaultExport_1 = false;
            if (ts.isFunctionDeclaration(node)) {
                name_1 = ((_b = node.name) === null || _b === void 0 ? void 0 : _b.text) || 'anonymous';
                var exportType = getExportType(node);
                isExport_1 = exportType !== null;
                isDefaultExport_1 = exportType === 'default';
            }
            else if (ts.isVariableDeclaration(node.parent)) {
                name_1 = node.parent.name.getText();
                // Check for export on variable declaration
                var statement = (_c = node.parent.parent) === null || _c === void 0 ? void 0 : _c.parent;
                if (ts.isVariableStatement(statement)) {
                    var exportType = getExportType(statement);
                    isExport_1 = exportType !== null;
                    isDefaultExport_1 = exportType === 'default';
                }
                // Check for separate export default
                if (!isExport_1) {
                    ts.forEachChild(sourceFile, function (child) {
                        if (ts.isExportAssignment(child) &&
                            ts.isIdentifier(child.expression) &&
                            child.expression.text === name_1) {
                            isExport_1 = true;
                            isDefaultExport_1 = true;
                        }
                    });
                }
            }
            if (name_1) {
                functions.push({
                    name: name_1,
                    line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
                    leadingComment: getLeadingComment(node, sourceFile),
                    parameters: getParameters(node),
                    isAsync: ((_d = node.modifiers) === null || _d === void 0 ? void 0 : _d.some(function (m) { return m.kind === ts.SyntaxKind.AsyncKeyword; })) || false,
                    isExport: isExport_1,
                    isDefaultExport: isDefaultExport_1,
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
var content = '';
process.stdin.on('data', function (chunk) {
    content += chunk;
});
process.stdin.on('end', function () {
    try {
        var sourceFile = ts.createSourceFile('temp.ts', content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
        var functions = extractFunctions(sourceFile);
        console.log(JSON.stringify(functions));
    }
    catch (error) {
        console.error("Failed to parse source: ".concat(error));
        process.exit(1);
    }
});
