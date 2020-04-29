/**
 * Try to render all Latex Math in the ANKI card
 * @throws Error if window.renderMathInElement wasn't found!
 */
function md2ankiRenderLaTeXMath() {
    console.debug("Md2Anki - LaTeXMath - Render");
    if (window.renderMathInElement !== undefined) {
        console.debug("Md2Anki - LaTeXMath - Render: renderMathInElement was found");
        renderMathInElement(document.querySelector('.card'), {
            delimiters: [{
                left: "$$",
                right: "$$",
                display: true
            }, {
                left: "$",
                right: "$",
                display: false
            }]
        });
    } else {
        throw Error("Md2Anki - LaTeXMath - Error: katex renderMathInElement was not found!");
    }
}

try {
    const scriptsToWaitFor = []
    for (let script of document.getElementsByTagName('script')) {
        if (script.src.startsWith("https://cdn.jsdelivr.net/npm/katex")) {
            scriptsToWaitFor.push(script)
        }
    }
    if (window.renderMathInElement !== undefined) {
        console.debug("Md2Anki - LaTeXMath - all scripts already loaded")
        // Execute the render method when everything is imported
        md2ankiRenderLaTeXMath()
    } else {
        Promise.all(scriptsToWaitFor.map(script => new Promise((resolve) => {
            console.debug("Md2Anki - LaTeXMath - wait for load:", script.src)
            script.addEventListener("load", () => {
                console.debug("Md2Anki - LaTeXMath - reached load:", script.src,
                    (window.renderMathInElement !== undefined) ? "(already ready to run)" : "")
                resolve()
            }, false)
        }))).then(() => {
            // Execute the render method when all connected scripts were loaded
            md2ankiRenderLaTeXMath()
        })
    }
} catch (e) {
    console.error(e)
}
