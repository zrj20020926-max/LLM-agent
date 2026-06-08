<template>
  <div class="markdown-content" v-html="renderState.html"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'
import 'highlight.js/styles/github.css'

const props = defineProps({
  content: {
    type: String,
    default: '',
  },
})

// 转义兜底，避免xss攻击
function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

// 将markdown的字符串转换成html，提交给highlight.js
function createMarkdownRenderer() {
  const markdown = new MarkdownIt({
    // 禁止 Markdown 中的原生 HTML，自动转义
    html: false,
    // 自动识别链接
    linkify: true,
    // 单个换行自动变 <br>
    breaks: true,
    highlight(code, language) {
      const trimmedLanguage = language?.trim()

      if (trimmedLanguage && hljs.getLanguage(trimmedLanguage)) {
        try {
          return hljs.highlight(code, {
            language: trimmedLanguage,
            ignoreIllegals: true,
          }).value
        } catch (error) {
          return escapeHtml(code)
        }
      }

      return hljs.highlightAuto(code).value
    },
  })

  // 重写代码块渲染结构
  markdown.renderer.rules.fence = (tokens, index, options, env, self) => {
    const token = tokens[index]
    const info = token.info ? token.info.trim() : ''
    const language = info.split(/\s+/g)[0]
    const highlighted = options.highlight
      ? options.highlight(token.content, language, '')
      : escapeHtml(token.content)
    const languageClass = language ? ` language-${escapeHtml(language)}` : ''
    const languageLabel = language ? `<span class="code-language">${escapeHtml(language)}</span>` : ''

    return `
      <div class="code-block">
        <div class="code-toolbar">
          ${languageLabel}
        </div>
        <pre><code class="hljs${languageClass}">${highlighted}</code></pre>
      </div>
    `
  }

  // 重写连接打开逻辑
  markdown.renderer.rules.link_open = (tokens, index, options, env, self) => {
    const token = tokens[index]
    const targetIndex = token.attrIndex('target')
    const relIndex = token.attrIndex('rel')

    if (targetIndex < 0) {
      token.attrPush(['target', '_blank'])
    } else {
      token.attrs[targetIndex][1] = '_blank'
    }

    if (relIndex < 0) {
      token.attrPush(['rel', 'noopener noreferrer'])
    } else {
      token.attrs[relIndex][1] = 'noopener noreferrer'
    }

    return self.renderToken(tokens, index, options)
  }

  return markdown
}

const renderState = computed(() => {
  const markdown = createMarkdownRenderer()
  const rawHtml = markdown.render(props.content || '')

  return {
    html: DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target', 'rel'],
    }),
  }
})
</script>

<style scoped>
.markdown-content {
  overflow-wrap: anywhere;
}

.markdown-content :deep(*) {
  max-width: 100%;
}

.markdown-content :deep(> :first-child) {
  margin-top: 0;
}

.markdown-content :deep(> :last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(p),
.markdown-content :deep(ul),
.markdown-content :deep(ol),
.markdown-content :deep(blockquote),
.markdown-content :deep(pre),
.markdown-content :deep(table) {
  margin: 0 0 12px;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 18px 0 10px;
  color: #111827;
  line-height: 1.35;
}

.markdown-content :deep(h1) {
  font-size: 22px;
}

.markdown-content :deep(h2) {
  font-size: 19px;
}

.markdown-content :deep(h3) {
  font-size: 17px;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 22px;
}

.markdown-content :deep(li + li) {
  margin-top: 4px;
}

.markdown-content :deep(blockquote) {
  padding: 2px 0 2px 12px;
  color: #4b5563;
  border-left: 3px solid #d1d5db;
}

.markdown-content :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(:not(pre) > code) {
  padding: 2px 5px;
  color: #b91c1c;
  font-size: 0.92em;
  border-radius: 5px;
  background: #fee2e2;
}

.markdown-content :deep(.code-block) {
  overflow: hidden;
  margin: 14px 0;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #f8fafc;
}

.markdown-content :deep(.code-toolbar) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 34px;
  padding: 6px 10px;
  color: #64748b;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
  background: #f1f5f9;
}

.markdown-content :deep(.code-language) {
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-content :deep(pre) {
  overflow-x: auto;
  margin: 0;
  padding: 14px;
  line-height: 1.6;
}

.markdown-content :deep(pre code) {
  padding: 0;
  white-space: pre;
  background: transparent;
}

.markdown-content :deep(table) {
  display: block;
  overflow-x: auto;
  border-collapse: collapse;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
}

.markdown-content :deep(th) {
  background: #f8fafc;
}
</style>
