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
    var currentClass = null;
    function visit(node) {
        var _a, _b, _c;
        if (ts.isClassDeclaration(node)) {
            var className_1 = ((_a = node.name) === null || _a === void 0 ? void 0 : _a.text) || 'AnonymousClass';
            currentClass = className_1;
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
                        name: methodName, // Just use the method name
                        line: sourceFile.getLineAndCharacterOfPosition(member.getStart()).line + 1,
                        leadingComment: getLeadingComment(member, sourceFile),
                        parameters: getParameters(member),
                        isAsync: ((_b = member.modifiers) === null || _b === void 0 ? void 0 : _b.some(function (m) { return m.kind === ts.SyntaxKind.AsyncKeyword; })) || false,
                        isExport: exportType_1 !== null,
                        isDefaultExport: exportType_1 === 'default',
                        nodeType: 'method',
                        className: className_1 // Add class name for reference
                    });
                }
            });
            currentClass = null;
        }
        else if (ts.isFunctionDeclaration(node)) {
            var name_1 = ((_b = node.name) === null || _b === void 0 ? void 0 : _b.text) || 'anonymous';
            var exportType = getExportType(node);
            functions.push({
                name: name_1,
                line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
                leadingComment: getLeadingComment(node, sourceFile),
                parameters: getParameters(node),
                isAsync: ((_c = node.modifiers) === null || _c === void 0 ? void 0 : _c.some(function (m) { return m.kind === ts.SyntaxKind.AsyncKeyword; })) || false,
                isExport: exportType !== null,
                isDefaultExport: exportType === 'default',
                nodeType: 'function'
            });
        }
        else if (ts.isVariableStatement(node)) {
            // Handle variable declarations that might be functions
            node.declarationList.declarations.forEach(function (decl) {
                var _a;
                if (ts.isVariableDeclaration(decl) && decl.initializer &&
                    (ts.isArrowFunction(decl.initializer) || ts.isFunctionExpression(decl.initializer))) {
                    var name_2 = decl.name.getText();
                    var exportType = getExportType(node);
                    var isExportDefault = node.parent && (ts.isExportAssignment(node.parent) ||
                        (node.parent.parent && ts.isExportAssignment(node.parent.parent)));
                    functions.push({
                        name: name_2,
                        line: sourceFile.getLineAndCharacterOfPosition(decl.getStart()).line + 1,
                        leadingComment: getLeadingComment(decl, sourceFile),
                        parameters: getParameters(decl.initializer),
                        isAsync: ((_a = decl.initializer.modifiers) === null || _a === void 0 ? void 0 : _a.some(function (m) { return m.kind === ts.SyntaxKind.AsyncKeyword; })) || false,
                        isExport: exportType !== null || isExportDefault,
                        isDefaultExport: exportType === 'default' || isExportDefault,
                        nodeType: 'function'
                    });
                }
            });
        }
        else if (ts.isExportAssignment(node)) {
            // Handle export default statements
            if (ts.isIdentifier(node.expression)) {
                var name_3 = node.expression.text;
                // Find the corresponding function and mark it as export default
                var func = functions.find(function (f) { return f.name === name_3; });
                if (func) {
                    func.isExport = true;
                    func.isDefaultExport = true;
                }
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
