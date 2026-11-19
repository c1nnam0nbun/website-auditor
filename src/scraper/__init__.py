import asyncio
import datetime
import json
import os
import sys
import time
from loguru import logger
from typing import Any, Literal
from abc import ABC, abstractmethod
from PIL import Image

from bs4 import BeautifulSoup

from .human import Humanization, HumanizationConfig

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from click import command, option

mcp = MCPServer("Demo")
context: Humanization

def prepare_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    tags_to_remove = ["script", "style", "link", "noscript", "svg"]
    attrs_to_remove = ["style"]

    for tag in soup.find_all(True):
        if tag.name in tags_to_remove: tag.decompose()
        if tag.attrs is not None:
            if tag.attrs.keys() & attrs_to_remove: 
                for attr in attrs_to_remove: del tag.attrs[attr]

    dt = str(datetime.datetime.now()).replace(" ", "T").replace(":", "-")
    file_name = f"snapshots/page_snapshot-{dt}.html"
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "x", encoding="utf-8") as file:
        file.write(str(soup))
        
    return f"Snapshot: {os.path.join(os.getcwd(), file_name)}"



@mcp.tool()
async def goto(url: str) -> str:
    """Opens the specified url in the browser. Returns simplified contents of the page"""
    logger.info(f"goto {url}")

    try:
        await context.page.goto(url)
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
        
    return prepare_text(content)


@mcp.tool()
async def contents() -> str:
    """Prints full contents of active page)"""
    logger.info("contents")
    return await context.page.content()


@mcp.tool()
async def hover(selector: str) -> str:
    """Hovers mouse over element specified by selector. Selector must be a valid CSS selector"""
    logger.info(f"hover {selector}")
    try:
        element = context.page.locator(selector).first
        await context.hover_at(element)
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


@mcp.tool()
async def click(selector: str, button: Literal["left", "right", "middle"] = "left") -> str:
    """Clicks on the element specified by selector with selected mouse button (left by default). Selector must be a valid CSS selector"""
    logger.info(f"click {selector} button:{button}")
    try:
        element = context.page.locator(selector).first
        await context.click_at(element, button)
        await context.page.wait_for_timeout(1000*5)
        await context.page.wait_for_load_state("networkidle")
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


@mcp.tool()
async def screenshot(full_page: bool = False, selector: str = "") -> str:
    """
    Creates screenshot of current page or element specified by selector and stores it in current directory.
    Selector must be a valid CSS selector
    """
    logger.info(f"screenshot full_page:{full_page} selector:{selector}")
    path = f"screenshots/{time.time_ns()}.jpeg"
    if len(selector) > 0:
        element = context.page.locator(selector).first
        await element.screenshot(path=path)
    else:
        await context.page.screenshot(full_page=full_page, path=path)

    with Image.open(path) as im:
        width, height = im.size
        width = max(width // 768, 1) * 768
        height = max(height // 768, 1) * 768
        im.thumbnail((width, height), resample=Image.Resampling.LANCZOS)
        im.save(path)
        
    return f"Screenshot: {os.path.join(os.getcwd(), path)}"


@mcp.tool()
async def type_text(text: str, selector: str = "") -> str:
    """
    Type the string of text. The target must be either previously clicked at or specified by the selector.
    Selector must be a valid CSS selector
    """
    logger.info(f"type {text} selector:{selector}")
    try:
        if len(selector) > 0:
            element = context.page.locator(selector).first
        else:
            element = await context.page.locator('*:focus')

        await context.type_at(element, text)
        await context.page.wait_for_load_state("networkidle")
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


@mcp.tool()
async def scroll_to_selector(selector: str) -> str:
    """
    Scroll the page to specified selector. Selector must be a valid CSS selector
    """
    logger.info(f"scroll_to_selector selector:{selector}")
    try:
        element = context.page.locator(selector).first
        await context.scroll_to(locator=element)
        await context.page.wait_for_load_state("networkidle")
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


@mcp.tool()
async def scroll_by_pixels(delta_y: int) -> str:
    """
    Scroll the page by the delta_y pixels. To scroll the element, use `hover` before `scroll`
    """
    logger.info(f"scroll delta_y:{delta_y}")
    try:
        await context.scroll_to(delta_y=delta_y)
        await context.page.wait_for_load_state("networkidle")
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


@mcp.tool()
async def back() -> str:
    """Go to the previous page"""
    try:
        await context.page.go_back()
        await context.page.wait_for_timeout(1000*5)
        await context.page.wait_for_load_state("networkidle")
        content = await context.page.content()
    except Exception as e:
        raise ToolError(e)
    return prepare_text(content)


class Provider(ABC):
    def __init__(self, model: str | None = None, effort: str | None = None):
        super().__init__()
        self.model = model
        self.effort = effort if effort else "medium"
        

    @abstractmethod
    async def start(self, env = os.environ) -> asyncio.subprocess.Process:
        ...

    @abstractmethod
    async def say(self, message: str, sink: asyncio.StreamWriter):
        sink.write(message)
        await sink.drain()


class AntigravityCLI(Provider):
    async def start(self, env = os.environ):
        args = [
            "agy",
            "--effort", self.effort,
            "--dangerously-skip-permissions", 
            "--input-format", "stream-json", 
            "--output-format", "stream-json", 
            "--add-dir", os.getcwd(),
            "--print-timeout", "30m",
        ]

        if self.model is not None:
            args.extend(["--model", self.model])

        return await asyncio.create_subprocess_exec(
            *args,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )

    async def say(self, message: str, sink: asyncio.StreamWriter):
        message = (json.dumps({ "event": "user", "message": { "content": message } }) + "\n").encode()
        await super().say(message, sink)


class ClaudeCode(Provider):
    async def start(self, env = os.environ):
        args = [
           "claude",
            "--print",
            "--effort", self.effort,
            "--dangerously-skip-permissions", 
            "--input-format", "stream-json",
            "--output-format", "stream-json", 
            "--add-dir", os.getcwd(),
            "--verbose",
        ]

        if self.model is not None:
            args.extend(["--model", self.model])

        return await asyncio.create_subprocess_exec(
            *args,
            env=env,
            limit=1024 * 1024,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )

    async def say(self, message: str, sink: asyncio.StreamWriter):
        message = (json.dumps({ "type": "user", "message": { "role": "user", "content": message } }) + "\n").encode()
        await super().say(message, sink)



async def init(
    port: int, 
    provider: Provider,
    env: os._Environ[str],
    website: str,
    workdir: str
):
    config = HumanizationConfig(
        fast=False,
        humanize=True,
        characters_per_minute=400,
        backspace_cpm=800,
        timeout=10000,
        stealth_mode=True,
        user_data_dir="./data"
    )
    
    async with Humanization(config) as ctx:
        global context
        context = ctx

        async def call_llm():
            process = await provider.start(env)
            message = f"/website-audit {website} \nThe working directory for the website is {workdir}, store all markdown and intermediate files there."
            
            from contextlib import chdir
            os.makedirs(workdir, exist_ok=True)
            with chdir(workdir):
                await provider.say(message, process.stdin)
                while True:
                    line = await process.stdout.readline()
                    if not line: break
                    line = line.decode().strip()
                    logger.debug(line)
                    try:
                        data = json.loads(line)
                        event = data.get("event")
                        if event == "result": break
                    except Exception as e:
                        logger.error(e)

                process.terminate()
                if process.returncode != 0:
                    err = await process.stderr.readline()
                    logger.error(err.decode().strip())


        task = asyncio.create_task(mcp.run_streamable_http_async(port=port, retry_interval=100))
        await call_llm()
        task.cancel()


@command()
@option("--port", default=3001, help="Port to listen on for HTTP")
@option(
    "--config",
    default="./config.json",
    help="Configuration file path"
)
@option(
    "--url",
    help="URL of the website to audit"
)
@option(
    "--workdir",
    help="Working directory for the website to use"
)
def main(port: int, config: str, url: str, workdir: str) -> int:
    logger.configure(
        handlers=[
            dict(sink=sys.stderr, level="INFO"),
            dict(sink="file.log"),
        ]
    )
    logger.info(f"Starting MCP Server on port {port}")
    logger.info(f"Endpoint will be: http://localhost:{port}/mcp")

    with open(config, "r", encoding="utf-8") as config_file:
        cfg: dict[str, Any] = json.loads(config_file.read())
        match cfg.get("provider"):
            case "claude": provider = ClaudeCode(cfg.get("model"), cfg.get("effort"))
            case "antigravity": provider = AntigravityCLI(cfg.get("model"), cfg.get("effort"))
            case None: raise Exception("\"provider\" must be set")
            case _: raise Exception(f"Unknown provider {cfg.get("provider")}")
        env = os.environ.copy()
        if cfg.get("env") is not None:
            for key, value in cfg.get("env").items():
                env[key] = value
    
    try:
        asyncio.run(init(port, provider, env, url, workdir))
    except asyncio.exceptions.CancelledError:
        pass

    return 0