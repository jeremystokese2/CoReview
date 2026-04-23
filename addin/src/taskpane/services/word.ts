/* global Word */

export async function getDocumentHtml(): Promise<string> {
  return Word.run(async (context) => {
    const body = context.document.body;
    const html = body.getHtml();
    await context.sync();
    return html.value;
  });
}
