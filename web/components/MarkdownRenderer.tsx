"use client";

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const parseMarkdown = (text: string) => {
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeContent = "";
    let codeLanguage = "";

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.startsWith("```")) {
        if (inCodeBlock) {
          elements.push(
            <pre key={`code-${i}`} className="bg-zinc-800 text-zinc-100 p-3 rounded-lg my-2 overflow-x-auto text-sm">
              <code>{codeContent}</code>
            </pre>
          );
          codeContent = "";
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
          codeLanguage = line.slice(3);
        }
        continue;
      }

      if (inCodeBlock) {
        codeContent += line + "\n";
        continue;
      }

      if (line.startsWith("**") && line.endsWith("**")) {
        elements.push(
          <p key={i} className="font-bold my-1">{line.replace(/\*\*/g, "")}</p>
        );
      } else if (line.startsWith("- ")) {
        elements.push(
          <li key={i} className="ml-4 my-1">{line.slice(2)}</li>
        );
      } else if (line.match(/^\d+\.\s/)) {
        elements.push(
          <li key={i} className="ml-4 my-1 list-decimal">{line.replace(/^\d+\.\s/, "")}</li>
        );
      } else if (line.trim() === "") {
        elements.push(<br key={i} />);
      } else {
        const formattedLine = line
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/g, "<em>$1</em>")
          .replace(/`(.*?)`/g, "<code class='bg-zinc-100 px-1 rounded text-sm'>$1</code>");

        elements.push(
          <p
            key={i}
            className="my-1"
            dangerouslySetInnerHTML={{ __html: formattedLine }}
          />
        );
      }
    }

    return elements;
  };

  return <div className="text-sm">{parseMarkdown(content)}</div>;
}