#!/usr/bin/env node
/**
 * Markdown to Notion Blocks Converter
 *
 * 使用 Martian 库将 Markdown 转换为 Notion API blocks
 * 从 stdin 读取 Markdown，输出 JSON 到 stdout
 */

const {markdownToBlocks} = require('@tryfabric/martian');

// 从 stdin 读取
let markdown = '';

process.stdin.setEncoding('utf8');
process.stdin.on('readable', () => {
  let chunk;
  while ((chunk = process.stdin.read()) !== null) {
    markdown += chunk;
  }
});

process.stdin.on('end', () => {
  try {
    const blocks = markdownToBlocks(markdown, {
      notionLimits: {
        truncate: true,  // 自动截断超长内容
      }
    });

    // 输出 JSON
    console.log(JSON.stringify(blocks));
  } catch (error) {
    console.error(JSON.stringify({
      error: error.message,
      stack: error.stack
    }));
    process.exit(1);
  }
});
