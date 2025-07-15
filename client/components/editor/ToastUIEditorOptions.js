import codeSyntaxHighlight from "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight-all.js";
import chart from "@toast-ui/editor-plugin-chart/dist/toastui-editor-plugin-chart.js";
import katex from "katex";
import router from "../../router.js";



const customHTMLRenderer = {
  // Add id attribute to headings
  heading(node, { entering, getChildrenText, origin }) {
    const original = origin();
    if (entering) {
      original.attributes = {
        id: getChildrenText(node)
          .toLowerCase()
          .replace(/[^a-z0-9-\s]*/g, "")
          .trim()
          .replace(/\s/g, "-"),
      };
    }
    return original;
  },
  // Convert relative hash links to absolute links
  link(_, { entering, origin }) {
    const original = origin();
    if (entering) {
      const href = original.attributes.href;
      if (href.startsWith("#")) {
        const targetRoute = {
          ...router.currentRoute.value,
          hash: href,
        };
        original.attributes.href = router.resolve(targetRoute).href;
      }
    }
    return original;
  },
  // KaTeX support for code blocks
  codeBlock(node, { origin }) {
    const original = origin();
    const { info, literal } = node;
    
    // Check if this is a KaTeX code block
    if (info === 'katex' || info === 'math') {
      try {
        const rendered = katex.renderToString(literal, {
          displayMode: true,
          throwOnError: false,
        });
        
        return {
          type: 'html',
          content: `<div class="katex-display">${rendered}</div>`
        };
      } catch (error) {
        console.error('KaTeX rendering error:', error);
        return original;
      }
    }
    
    return original;
  },
  // KaTeX support for inline math in text
  text(node, { origin }) {
    const original = origin();
    const content = node.literal;
    
    // Check for inline math patterns: $...$ or \(...\)
    const inlineMathPattern = /\$([^$\n]+?)\$|\\\(([^)\n]+?)\\\)/g;
    let match;
    let lastIndex = 0;
    let hasMath = false;
    let result = '';
    
    while ((match = inlineMathPattern.exec(content)) !== null) {
      hasMath = true;
      // Add text before the math
      result += content.substring(lastIndex, match.index);
      
      // Extract the math content
      const mathContent = match[1] || match[2];
      
      try {
        const rendered = katex.renderToString(mathContent, {
          displayMode: false,
          throwOnError: false,
        });
        
        result += rendered;
      } catch (error) {
        console.error('KaTeX inline rendering error:', error);
        result += match[0];
      }
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < content.length) {
      result += content.substring(lastIndex);
    }
    
    // If math was found, return HTML content
    if (hasMath) {
      return {
        type: 'html',
        content: result
      };
    }
    
    return original;
  }
};

const baseOptions = {
  height: "auto",
  plugins: [codeSyntaxHighlight, chart],
  customHTMLRenderer: customHTMLRenderer,
  usageStatistics: false,
  toolbarItems: [
    ['task', 'table', 'image', 'link', 'codeblock'],
  ],
  hideModeSwitch: true,
};

// Function to get options with specific previewStyle
function getEditorOptions(previewStyle = 'vertical') {
  return {
    ...baseOptions,
    previewStyle: previewStyle,
  };
}

export default baseOptions;
export { getEditorOptions };

