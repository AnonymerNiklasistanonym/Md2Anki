/**
 * Try to render source code parts in the ANKI card
 * @throws Error if hljs or its used components weren't found!
 */
function md2ankiRenderSourceCode() {
    console.debug("Md2Anki - SourceCode - Render");
    if (window.hljs !== undefined) {
        if (hljs.highlightBlock !== undefined) {
            console.debug("Md2Anki -  SourceCode - Render: hljs was found")
            document.querySelectorAll('.card pre code').forEach(block => {
                hljs.highlightBlock(block)
            })
        } else {
            throw Error("Md2Anki - SourceCode - Error: hljs.highlightBlock was not found!")
        }
    } else {
        throw Error("Md2Anki - SourceCode - Error: hljs was not found!")
    }
}

// const HLJS_VERSION = '10.0.1'
// const HLJS_URL = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${HLJS_VERSION}/highlight.min.js`
// const HLJS_FILE_NAME = `highlight_${HLJS_VERSION}.min.js`
//
// const hljs = document.querySelector(`script[src="${HLJS_URL}"]`)
// console.log("--------------")
// console.log(hljs)
// console.log("--------------")

try {
    const scriptsToWaitFor = []
    for (let script of document.getElementsByTagName('script')) {
        if (script.src.startsWith("https://cdnjs.cloudflare.com/ajax/libs/highlight.js")) {
            scriptsToWaitFor.push(script)
        }
    }
    if (window.hljs !== undefined && hljs.highlightBlock !== undefined) {
        console.debug("Md2Anki - SourceCode - all scripts already loaded")
        // Execute the render method when everything is imported
        md2ankiRenderSourceCode()
    } else {
        Promise.all(scriptsToWaitFor.map(script => new Promise((resolve) => {
            console.debug("Md2Anki - SourceCode - wait for load:", script.src)
            script.addEventListener("load", () => {
                console.debug("Md2Anki - SourceCode - reached load:", script.src,
                    (window.hljs !== undefined && hljs.highlightBlock !== undefined) ? "(already ready to run)" : "")
                resolve()
            }, false)
        }))).then(() => {
            // Execute the render method when all connected scripts were loaded
            md2ankiRenderSourceCode()
        })
    }
} catch (e) {
    console.error(e)
}
