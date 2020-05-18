/**
 * Try to render all Latex Math in the ANKI card
 * @throws Error if window.renderMathInElement wasn't found!
 */
function md2ankiRenderLaTeXMath() {
    console.debug("Md2Anki - LaTeXMath - Render")
    if (window.renderMathInElement !== undefined) {
        console.debug("Md2Anki - LaTeXMath - Render: renderMathInElement was found")
        Array.from(document.getElementsByClassName("math")).forEach(element => {
            console.debug("Md2Anki - LaTeXMath - update math element", element)
            renderMathInElement(element, {
                delimiters: [{
                    left: "$$",
                    right: "$$",
                    display: true
                }, {
                    left: "$",
                    right: "$",
                    display: false
                }]
            })
        })
    } else {
        throw Error("Md2Anki - LaTeXMath - Error: katex renderMathInElement was not found!")
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
        if (document.readyState === "complete") {
            console.debug("Md2Anki - LaTeXMath - dom is ready")
            md2ankiRenderLaTeXMath()
        } else {
            console.debug("Md2Anki - LaTeXMath - dom not yet ready")
            window.addEventListener('load', () => {
                console.debug("Md2Anki - LaTeXMath - dom is ready")
                md2ankiRenderLaTeXMath()
            })
        }
    } else {
        Promise.all(scriptsToWaitFor.map(script => new Promise((resolve, reject) => {
            console.debug("Md2Anki - LaTeXMath - wait for load:", script.src)
            script.addEventListener("load", () => {
                console.debug("Md2Anki - LaTeXMath - reached load:", script.src)
                if (window.renderMathInElement !== undefined) {
                    reject("Md2Anki - LaTeXMath - some sources were loaded but already ready to run")
                } else {
                    resolve()
                }
            }, false)
        })))
        .then(() => {
            console.debug("Md2Anki - LaTeXMath - all sources were loaded")
            md2ankiRenderLaTeXMath()
        })
        .catch(err => {
            // Catch error but still try to render
            console.debug(err)
            md2ankiRenderLaTeXMath()
        })
    }
} catch (e) {
    console.error(e)
}
