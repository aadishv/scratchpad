import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import {
  TextNode,
  EditorState,
  EditorConfig,
} from 'lexical';
import './MarkdownEditor.css';

// Custom TextNode that handles markdown syntax highlighting
class MarkdownTextNode extends TextNode {
  static getType(): string {
    return 'markdown-text';
  }

  static clone(node: MarkdownTextNode): MarkdownTextNode {
    return new MarkdownTextNode(node.__text, node.__key);
  }

  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    this.updateDOM(this, dom, config);
    return dom;
  }

  updateDOM(_prevNode: MarkdownTextNode, dom: HTMLElement, _config: EditorConfig): boolean {
    const text = this.getTextContent();
    
    // Clear existing content
    dom.innerHTML = '';
    
    // Parse markdown syntax and create spans
    this.parseMarkdown(text, dom);
    
    return false;
  }

  parseMarkdown(text: string, container: HTMLElement): void {
    let pos = 0;
    const len = text.length;
    
    while (pos < len) {
      let matched = false;
      
      // Try to match markdown patterns
      // Bold: **text** or __text__
      if (pos + 4 <= len) {
        if ((text.slice(pos, pos + 2) === '**' || text.slice(pos, pos + 2) === '__')) {
          const delimiter = text.slice(pos, pos + 2);
          const closePos = text.indexOf(delimiter, pos + 2);
          if (closePos !== -1 && closePos > pos + 2) {
            // Opening delimiter
            const openSpan = document.createElement('span');
            openSpan.className = 'markdown-syntax';
            openSpan.textContent = delimiter;
            container.appendChild(openSpan);
            
            // Bold content
            const contentSpan = document.createElement('span');
            contentSpan.className = 'markdown-bold';
            contentSpan.textContent = text.slice(pos + 2, closePos);
            container.appendChild(contentSpan);
            
            // Closing delimiter
            const closeSpan = document.createElement('span');
            closeSpan.className = 'markdown-syntax';
            closeSpan.textContent = delimiter;
            container.appendChild(closeSpan);
            
            pos = closePos + 2;
            matched = true;
          }
        }
      }
      
      // Italic: *text* or _text_ (single char)
      if (!matched && pos + 2 <= len) {
        if ((text[pos] === '*' && text[pos + 1] !== '*') || 
            (text[pos] === '_' && text[pos + 1] !== '_')) {
          const delimiter = text[pos];
          let closePos = pos + 1;
          
          // Find closing delimiter, avoiding ** or __
          while (closePos < len) {
            if (text[closePos] === delimiter) {
              // Make sure it's not part of ** or __
              if ((closePos + 1 >= len || text[closePos + 1] !== delimiter) &&
                  (closePos - 1 < pos || text[closePos - 1] !== delimiter)) {
                break;
              }
            }
            closePos++;
          }
          
          if (closePos < len && closePos > pos + 1) {
            // Opening delimiter
            const openSpan = document.createElement('span');
            openSpan.className = 'markdown-syntax';
            openSpan.textContent = delimiter;
            container.appendChild(openSpan);
            
            // Italic content
            const contentSpan = document.createElement('span');
            contentSpan.className = 'markdown-italic';
            contentSpan.textContent = text.slice(pos + 1, closePos);
            container.appendChild(contentSpan);
            
            // Closing delimiter
            const closeSpan = document.createElement('span');
            closeSpan.className = 'markdown-syntax';
            closeSpan.textContent = delimiter;
            container.appendChild(closeSpan);
            
            pos = closePos + 1;
            matched = true;
          }
        }
      }
      
      // Strikethrough: ~~text~~
      if (!matched && pos + 4 <= len) {
        if (text.slice(pos, pos + 2) === '~~') {
          const closePos = text.indexOf('~~', pos + 2);
          if (closePos !== -1 && closePos > pos + 2) {
            // Opening delimiter
            const openSpan = document.createElement('span');
            openSpan.className = 'markdown-syntax';
            openSpan.textContent = '~~';
            container.appendChild(openSpan);
            
            // Strikethrough content
            const contentSpan = document.createElement('span');
            contentSpan.className = 'markdown-strikethrough';
            contentSpan.textContent = text.slice(pos + 2, closePos);
            container.appendChild(contentSpan);
            
            // Closing delimiter
            const closeSpan = document.createElement('span');
            closeSpan.className = 'markdown-syntax';
            closeSpan.textContent = '~~';
            container.appendChild(closeSpan);
            
            pos = closePos + 2;
            matched = true;
          }
        }
      }
      
      // Heading: # at start of line
      if (!matched && (pos === 0 || text[pos - 1] === '\n')) {
        let hashCount = 0;
        let tempPos = pos;
        while (tempPos < len && text[tempPos] === '#' && hashCount < 6) {
          hashCount++;
          tempPos++;
        }
        
        if (hashCount > 0 && tempPos < len && text[tempPos] === ' ') {
          // Hash symbols
          const hashSpan = document.createElement('span');
          hashSpan.className = 'markdown-syntax';
          hashSpan.textContent = text.slice(pos, tempPos + 1);
          container.appendChild(hashSpan);
          
          // Find end of line
          let endPos = text.indexOf('\n', tempPos + 1);
          if (endPos === -1) endPos = len;
          
          // Heading content
          const contentSpan = document.createElement('span');
          contentSpan.className = `markdown-heading markdown-h${hashCount}`;
          contentSpan.textContent = text.slice(tempPos + 1, endPos);
          container.appendChild(contentSpan);
          
          pos = endPos;
          matched = true;
        }
      }
      
      // List: - or * at start of line
      if (!matched && (pos === 0 || text[pos - 1] === '\n')) {
        if ((text[pos] === '-' || text[pos] === '*') && 
            pos + 1 < len && text[pos + 1] === ' ') {
          // Bullet
          const bulletSpan = document.createElement('span');
          bulletSpan.className = 'markdown-syntax';
          bulletSpan.textContent = text.slice(pos, pos + 2);
          container.appendChild(bulletSpan);
          
          // Find end of line
          let endPos = text.indexOf('\n', pos + 2);
          if (endPos === -1) endPos = len;
          
          // List item content
          const contentSpan = document.createElement('span');
          contentSpan.className = 'markdown-list-item';
          contentSpan.textContent = text.slice(pos + 2, endPos);
          container.appendChild(contentSpan);
          
          pos = endPos;
          matched = true;
        }
      }
      
      // Numbered list: digit. at start of line
      if (!matched && (pos === 0 || text[pos - 1] === '\n')) {
        let tempPos = pos;
        let hasDigit = false;
        while (tempPos < len && text[tempPos] >= '0' && text[tempPos] <= '9') {
          hasDigit = true;
          tempPos++;
        }
        
        if (hasDigit && tempPos < len && text[tempPos] === '.' && 
            tempPos + 1 < len && text[tempPos + 1] === ' ') {
          // Number and dot
          const numberSpan = document.createElement('span');
          numberSpan.className = 'markdown-syntax';
          numberSpan.textContent = text.slice(pos, tempPos + 2);
          container.appendChild(numberSpan);
          
          // Find end of line
          let endPos = text.indexOf('\n', tempPos + 2);
          if (endPos === -1) endPos = len;
          
          // List item content
          const contentSpan = document.createElement('span');
          contentSpan.className = 'markdown-list-item';
          contentSpan.textContent = text.slice(tempPos + 2, endPos);
          container.appendChild(contentSpan);
          
          pos = endPos;
          matched = true;
        }
      }
      
      // No match, add regular character
      if (!matched) {
        const textNode = document.createTextNode(text[pos]);
        container.appendChild(textNode);
        pos++;
      }
    }
  }

  static importJSON(serializedNode: any): MarkdownTextNode {
    return new MarkdownTextNode(serializedNode.text);
  }

  exportJSON(): any {
    return {
      ...super.exportJSON(),
      type: 'markdown-text',
      version: 1,
    };
  }
}

// Plugin to convert all TextNodes to MarkdownTextNodes
function MarkdownPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerNodeTransform(TextNode, (textNode: TextNode) => {
      if (!(textNode instanceof MarkdownTextNode)) {
        const markdownNode = new MarkdownTextNode(textNode.getTextContent());
        textNode.replace(markdownNode);
      }
    });
  }, [editor]);

  return null;
}

const theme = {
  paragraph: 'editor-paragraph',
  text: {
    bold: 'editor-text-bold',
    italic: 'editor-text-italic',
    strikethrough: 'editor-text-strikethrough',
  },
};

function onError(error: Error) {
  console.error(error);
}

export default function MarkdownEditor() {
  const initialConfig = {
    namespace: 'MarkdownEditor',
    theme,
    onError,
    nodes: [MarkdownTextNode],
  };

  const onChange = (_editorState: EditorState) => {
    // You can handle the markdown text here if needed
  };

  return (
    <LexicalComposer initialConfig={initialConfig}>
      <div className="editor-container">
        <RichTextPlugin
          contentEditable={<ContentEditable className="editor-input" />}
          placeholder={
            <div className="editor-placeholder">
              Enter some markdown text...
              <br />
              <br />
              Try: **bold**, *italic*, ~~strikethrough~~
              <br />
              # Heading 1, ## Heading 2
              <br />
              - List item, 1. Numbered list
            </div>
          }
          ErrorBoundary={LexicalErrorBoundary}
        />
        <HistoryPlugin />
        <OnChangePlugin onChange={onChange} />
        <MarkdownPlugin />
      </div>
    </LexicalComposer>
  );
}
