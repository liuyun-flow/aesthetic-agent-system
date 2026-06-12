"use client";

import Link from "next/link";
import { useState } from "react";
import { useT } from "@/i18n";

type FaqItem = {
  q: { zh: string; en: string };
  a: { zh: string; en: string };
};

const FAQ_ITEMS: FaqItem[] = [
  {
    q: {
      zh: "为什么自动图片描述不准？",
      en: "Why is the auto-generated image description inaccurate?",
    },
    a: {
      zh: "图片描述依赖 OpenAI GPT-4o-mini 的视觉能力。它对复杂设计的细节识别有限，可能遗漏字体选择、材质质感、微妙色彩变化等。建议把自动描述作为起点，然后手动补充关键细节。如果使用占位模式（placeholder），描述完全是示例数据，不匹配你的图片。",
      en: "Image descriptions rely on OpenAI GPT-4o-mini's vision capability, which has limited ability to recognize fine details in complex designs. It may miss font choices, material textures, subtle color variations, etc. Use the auto-description as a starting point and manually add key details. If using placeholder mode, descriptions are sample data and won't match your images at all.",
    },
  },
  {
    q: {
      zh: "为什么提示未配置 API Key？",
      en: "Why does it say API Key not configured?",
    },
    a: {
      zh: "这个工具需要两个 API Key 才能完整运行：1) DeepSeek API Key — 用于审美分析、评分、迭代等推理任务；2) OpenAI API Key — 用于图片自动描述（可选，可以使用占位模式跳过）。请前往「设置」页面配置这些 Key。Key 保存在你本地机器的 backend/data/config/ 目录中，不会上传。",
      en: "This tool needs two API keys to run fully: 1) DeepSeek API Key — for aesthetic analysis, critique, iteration, and other reasoning tasks; 2) OpenAI API Key — for auto image description (optional; can use placeholder mode). Go to the Settings page to configure these keys. Keys are stored locally in your backend/data/config/ directory and are never uploaded.",
    },
  },
  {
    q: {
      zh: "DeepSeek 和 OpenAI Vision 分别负责什么？",
      en: "What do DeepSeek and OpenAI Vision each do?",
    },
    a: {
      zh: "DeepSeek 是「审美大脑」——它读取你的文字描述，进行 9 维度美学分析、结构化评分、设计问题诊断、改版方向生成、判断差异对比、训练画像生成等。OpenAI Vision 是「眼睛」——它把你上传的图片转成结构化的文字描述（风格、颜色、构图、潜在问题），供 DeepSeek 使用。两者职责分离：Vision 负责「看懂图」，DeepSeek 负责「审美判断」。",
      en: "DeepSeek is the 'aesthetic brain' — it reads your text description and performs 9-dimension aesthetic analysis, structured scoring, design issue diagnosis, iteration direction generation, judgment gap comparison, training profile generation, etc. OpenAI Vision is the 'eyes' — it converts your uploaded images into structured text descriptions (style, colors, composition, potential issues) for DeepSeek to use. The two have separate roles: Vision handles 'seeing the image', DeepSeek handles 'aesthetic judgment'.",
    },
  },
  {
    q: {
      zh: "placeholder 是什么意思？",
      en: "What does 'placeholder' mean?",
    },
    a: {
      zh: "占位模式（placeholder）是一个免 API Key 的模式。当你没有配置 OpenAI API Key 时，系统会返回固定的示例描述，而不是真正识别你的图片。这意味着：你可以体验完整的训练流程，但图片描述不会匹配你的实际图片，AI 的分析也是基于示例描述进行的。适合初次体验，但不适合真正的审美训练。建议尽快配置真实的 OpenAI API Key。",
      en: "Placeholder mode is a no-API-key mode. When you haven't configured an OpenAI API Key, the system returns fixed sample descriptions instead of actually recognizing your images. This means: you can experience the full training workflow, but image descriptions won't match your actual images, and AI analysis is based on sample descriptions. Good for first-time exploration, but not suitable for real aesthetic training. Configure a real OpenAI API Key as soon as possible.",
    },
  },
  {
    q: {
      zh: "我的数据存在哪里？",
      en: "Where is my data stored?",
    },
    a: {
      zh: "所有数据都存储在你本地机器的 backend/data/ 目录中：训练记录和案例存在 data/database/aesthetic.db（SQLite 文件）；上传的图片存在 data/uploads/（UUID 命名）；API Key 和设置存在 data/config/app_config.json。没有任何数据上传到云端或第三方服务器。你可以随时备份整个 data/ 目录。",
      en: "All data is stored locally on your machine in the backend/data/ directory: training records and cases in data/database/aesthetic.db (SQLite file); uploaded images in data/uploads/ (UUID-named files); API keys and settings in data/config/app_config.json. No data is uploaded to the cloud or third-party servers. You can back up the entire data/ directory at any time.",
    },
  },
  {
    q: {
      zh: "API Key 会不会暴露？",
      en: "Could my API Key be exposed?",
    },
    a: {
      zh: "不会。API Key 仅保存在你的本地机器上（backend/data/config/app_config.json 或 .env 文件）。后端 API 返回时 Key 会被脱敏（例如 sk-a***3f8b），前端只会看到「已配置/未配置」的状态标识。Key 只在调用对应模型服务时使用，不会发送给任何其他第三方。",
      en: "No. API keys are stored only on your local machine (backend/data/config/app_config.json or .env file). The backend API returns masked keys (e.g., sk-a***3f8b), and the frontend only sees 'Configured/Not configured' status indicators. Keys are only used when calling the corresponding model service and are never sent to any other third party.",
    },
  },
  {
    q: {
      zh: "为什么要先自评？",
      en: "Why should I self-assess first?",
    },
    a: {
      zh: "这是审美训练的核心机制。如果你直接看 AI 的分析结果，你的大脑会不自觉地接受 AI 的观点——这不是训练，是被动接收。先自己打分、写优缺点、判断目标用户和价格带，然后再看 AI 的判断，你才能发现：哪些你注意到了、哪些你漏掉了、哪些你判断错了。这个「判断差异」就是学习的起点。记住：AI 的观点不一定对，它只是给你一个外部参照系。",
      en: "This is the core mechanism of aesthetic training. If you see AI's analysis first, your brain will unconsciously accept AI's viewpoint — that's not training, it's passive reception. Score first, write your own strengths and weaknesses, judge the target audience and price band, then compare with AI's judgment. This is how you discover: what you noticed, what you missed, what you misjudged. The 'judgment gap' is where learning begins. Remember: AI's opinion isn't necessarily right — it just gives you an external reference frame.",
    },
  },
  {
    q: {
      zh: "怎么判断训练是否有效？",
      en: "How do I know if the training is working?",
    },
    a: {
      zh: "几个信号可以判断训练是否有效：1) 你的评分和 AI 评分的差距在缩小（说明你的判断标准在向行业标准靠拢）；2) 你能在 AI 指出之前就发现更多问题（说明你的眼力在提升）；3) 你不再需要「分析」功能就能自己拆解一个设计的好坏（内在化了审美框架）；4) 你的参考案例库在增长，且你能清晰说出每个案例好/坏在哪里。训练工作台的统计面板和每周复盘可以帮你追踪这些变化。",
      en: "Several signs indicate effective training: 1) The gap between your scores and AI scores is narrowing (your judgment is aligning with professional standards); 2) You can spot more issues before AI points them out (your eye is improving); 3) You can break down a design's quality without needing the 'Analyze' function (you've internalized the aesthetic framework); 4) Your reference case library is growing and you can clearly articulate why each case is good/bad. The Training Workbench stats panel and weekly review help track these changes.",
    },
  },
  {
    q: { zh: "Embedding 是什么？需要配置吗？", en: "What is Embedding? Do I need it?" },
    a: {
      zh: "Embedding 是把案例文本转成高维向量的技术，用于语义搜索。它不是必须项。不配置 Embedding 时，普通筛选（按分类、审美等级、价格带）仍然可用。配置后，你可以用自然语言搜索案例库，例如输入「高考直播封面，年轻有冲击力但不要廉价」，系统会找到风格相似的案例。需要 OpenAI API Key 和 EMBEDDING_PROVIDER=openai 配置。配置后需要在参考案例面板点击「重建索引」。",
      en: "Embedding converts case text into high-dimensional vectors for semantic search. It is optional. Without it, regular filters (by category, aesthetic level, price band) still work. With it enabled, you can search using natural language like 'young, impactful design without looking cheap'. Requires OpenAI API Key and EMBEDDING_PROVIDER=openai. After configuring, click 'Rebuild Index' in the Reference Case panel.",
    },
  },
  {
    q: { zh: "语义搜索和普通筛选有什么区别？", en: "Semantic search vs regular filters?" },
    a: {
      zh: "普通筛选是按分类、审美等级、价格带精确匹配。语义搜索是按含义匹配——找到「感觉相似」的案例，即使标签不完全匹配。语义搜索需要先配置 Embedding。如果未配置，搜索框输入后会自动降级为普通筛选，不会报错。",
      en: "Regular filters match exactly by category, aesthetic level, and price band. Semantic search matches by meaning — finding cases that 'feel similar' even if tags don't match exactly. Semantic search requires Embedding to be configured. If not configured, the search gracefully falls back to regular filters.",
    },
  },
  {
    q: { zh: "为什么打开页面白屏或崩溃？", en: "Why does the page go blank or crash?" },
    a: {
      zh: "这通常是浏览器缓存了旧版页面资源导致的。系统已内置自动恢复：首次遇到资源加载失败会自动刷新。如果仍白屏，请按 Ctrl+F5 强制刷新，或清除浏览器最近一小时的缓存。如果使用 Docker 部署，可以运行 docker compose restart frontend 重启前端服务。",
      en: "This is usually caused by the browser caching old page resources. The system has built-in recovery: it auto-refreshes on first resource load failure. If still blank, press Ctrl+F5 to force refresh, or clear browser cache for the last hour. For Docker deployments, run docker compose restart frontend.",
    },
  },
  {
    q: { zh: "Windows 下双击 start.bat 打不开怎么办？", en: "What if start.bat won't run on Windows?" },
    a: {
      zh: "1) 确认已安装 Docker Desktop 并且正在运行（右下角任务栏有 Docker 图标）。2) 如果双击闪退，右键点击 start.bat，选择「以管理员身份运行」。3) 如果提示「未检测到 Docker」，打开命令提示符（cmd）输入 docker --version 确认 Docker 已加入 PATH。4) 仍然不行的话，在终端中 cd 到项目目录，手动执行 docker compose up --build。",
      en: "1) Make sure Docker Desktop is installed and running (check the taskbar for the Docker icon). 2) If it flashes and closes, right-click start.bat and select 'Run as administrator'. 3) If it says Docker not found, open Command Prompt and type docker --version to verify Docker is in PATH. 4) If all else fails, cd to the project directory in terminal and run docker compose up --build manually.",
    },
  },
  {
    q: { zh: "Docker 没安装怎么用？", en: "How to use without Docker?" },
    a: {
      zh: "本工具推荐使用 Docker 部署。如果你无法安装 Docker，可以使用本地开发模式：后端需要 Python 3.11+，运行 pip install -r backend/requirements.txt 然后 uvicorn app.main:app --host 127.0.0.1 --port 8000。前端需要 Node.js 18+，运行 npm install 然后 npm run dev。详见 README.md 中的本地开发说明。",
      en: "Docker is the recommended deployment method. If you cannot install Docker, use local dev mode: Backend requires Python 3.11+, run pip install -r backend/requirements.txt then uvicorn app.main:app. Frontend requires Node.js 18+, run npm install then npm run dev. See README.md for detailed local dev instructions.",
    },
  },
];

export default function HelpPage() {
  const { t, lang } = useT();
  const zh = lang !== "en";
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (i: number) => setOpenFaq(openFaq === i ? null : i);

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-xl font-semibold mb-6">
        {zh ? "帮助中心" : "Help Center"}
      </h1>

      {/* Quick links */}
      <div className="flex flex-wrap gap-2 mb-8">
        <Link
          href="/setup"
          className="rounded bg-blue-100 px-3 py-2 text-xs font-medium text-blue-700 hover:bg-blue-200 transition"
        >
          {zh ? "🪄 打开首次使用向导" : "🪄 Open Setup Wizard"}
        </Link>
        <Link
          href="/settings"
          className="rounded border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 transition"
        >
          {zh ? "⚙️ 去设置页面" : "⚙️ Go to Settings"}
        </Link>
        <Link
          href="/"
          className="rounded border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 transition"
        >
          {zh ? "🏋️ 去训练工作台" : "🏋️ Go to Workbench"}
        </Link>
      </div>

      {/* Sections */}
      <div className="space-y-8">
        {/* Quick Start */}
        <Section
          title={zh ? "快速开始" : "Quick Start"}
          icon="🚀"
        >
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
            <li>
              {zh
                ? "配置 API Key：打开设置页面，填入 DeepSeek 和 OpenAI 的 API Key，点击测试确认连接成功。"
                : "Configure API Keys: Open Settings, enter your DeepSeek and OpenAI API keys, click Test to confirm."}
            </li>
            <li>
              {zh
                ? "上传一张图片：在工作台点击上传区域，上传一张你想分析的设计作品。"
                : "Upload an image: On the workbench, click the upload area and select a design work to analyze."}
            </li>
            <li>
              {zh
                ? "自动生成描述：点击「自动生成图片描述」，等待 AI 把图片内容转成文字。"
                : "Auto-generate description: Click 'Auto-generate description' and wait for AI to convert the image to text."}
            </li>
            <li>
              {zh
                ? "填写自评：点击「+ 填写我的初步判断」，打分、写优缺点、填目标用户和价格带。"
                : "Self-assess: Click '+ Add my own judgment', score, write strengths/weaknesses, target audience, and price band."}
            </li>
            <li>
              {zh
                ? "选择任务类型（分析/评分/迭代），点击运行。"
                : "Choose task type (Analyze/Critique/Iterate) and click Run."}
            </li>
            <li>
              {zh
                ? "查看结果和判断差异，记录你学到了什么。"
                : "Review results and judgment gap. Record what you learned."}
            </li>
          </ol>
        </Section>

        {/* Shortcuts & conveniences */}
        <Section
          title={zh ? "快捷操作" : "Shortcuts & Conveniences"}
          icon="⚡"
        >
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
            <li>
              {zh
                ? "粘贴截图：在工作台任意位置按 Ctrl+V，可直接上传剪贴板中的截图；也可以把图片文件拖拽到图片区域。"
                : "Paste screenshots: Press Ctrl+V anywhere on the workbench to upload an image from your clipboard, or drag an image file onto the image area."}
            </li>
            <li>
              {zh
                ? "自动描述：配置好 Vision 后，上传图片会自动生成中文描述，无需再点按钮。"
                : "Auto description: With Vision configured, uploaded images are described automatically — no extra click."}
            </li>
            <li>
              {zh
                ? "快速提交：在作品描述框内按 Ctrl+Enter 直接运行当前任务。"
                : "Quick submit: Press Ctrl+Enter inside the description box to run the current task."}
            </li>
            <li>
              {zh
                ? "取消请求：AI 分析等待过久时，点击进度条右侧的「取消」按钮即可中断。"
                : "Cancel: If an AI call takes too long, click 'Cancel' next to the progress indicator."}
            </li>
            <li>
              {zh
                ? "再练一次：打开历史记录详情，点击「再练一次」把当时的作品描述载入表单，重新自评并对比你过去的判断。"
                : "Practice again: Open a session's detail and click 'Practice again' to reload its description, judge it again, and compare with your past self."}
            </li>
            <li>
              {zh
                ? "折叠面板：工作台的「今日训练」「参考案例库」「最近训练记录」都可以点击标题栏收起或展开，状态会被记住。"
                : "Collapsible panels: Training, Reference Library, and Recent Sessions can be collapsed via their header bars; your choice is remembered."}
            </li>
          </ul>
        </Section>

        {/* Configure API Keys */}
        <Section
          title={zh ? "如何配置 API Key" : "How to Configure API Keys"}
          icon="🔑"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "前往「设置」页面，填写以下信息："
                : "Go to the Settings page and fill in:"}
            </p>
            <ul className="list-disc list-inside space-y-2">
              <li>
                <b>DeepSeek API Key</b>:{" "}
                {zh
                  ? "在 platform.deepseek.com 注册并创建 API Key（以 sk- 开头）。填入 API Key 栏，点击「测试连接」。"
                  : "Register at platform.deepseek.com and create an API Key (starts with sk-). Enter it and click 'Test Connection'."}
              </li>
              <li>
                <b>OpenAI API Key</b>:{" "}
                {zh
                  ? "在 platform.openai.com 注册并创建 API Key（以 sk- 开头，需要充值）。在 Vision 配置区填入。如果没有 OpenAI Key，可以先选择「占位」提供者跳过。"
                  : "Register at platform.openai.com and create an API Key (starts with sk-, requires credits). Fill in under Vision config. If you don't have one, select 'Placeholder' provider to skip."}
              </li>
            </ul>
            <p className="text-xs text-gray-400">
              {zh
                ? "所有 Key 保存在 backend/data/config/app_config.json，不会上传到任何服务器。"
                : "All keys are stored in backend/data/config/app_config.json and never uploaded to any server."}
            </p>
          </div>
        </Section>

        {/* Training Flow */}
        <Section
          title={zh ? "如何完成一次训练" : "How to Complete a Training"}
          icon="🏋️"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "一次完整的训练包含以下环节："
                : "A complete training session includes:"}
            </p>
            <ol className="list-decimal list-inside space-y-2">
              <li>
                <b>{zh ? "上传图片" : "Upload"}</b> — {zh ? "jpg/png/webp，最大 10MB" : "jpg/png/webp, max 10MB"}
              </li>
              <li>
                <b>{zh ? "自动生成描述" : "Auto-describe"}</b> — {zh ? "AI 把图片转成结构化文字描述" : "AI converts image to structured text description"}
              </li>
              <li>
                <b>{zh ? "填写作品描述" : "Write description"}</b> — {zh ? "补充颜色、布局、字体、材质、氛围等细节" : "Add colors, layout, fonts, materials, mood details"}
              </li>
              <li>
                <b>{zh ? "自评" : "Self-assess"}</b> — {zh ? "先打分，写优缺点，判断目标用户和价格带" : "Score first, write strengths/weaknesses, target audience, price band"}
              </li>
              <li>
                <b>{zh ? "选择任务并运行" : "Choose task and run"}</b>
              </li>
              <li>
                <b>{zh ? "查看判断差异" : "Review judgment gap"}</b> — {zh ? "对比你和 AI 的差异，记录学习" : "Compare your judgment vs AI, record learning"}
              </li>
              <li>
                <b>{zh ? "标记完成" : "Mark complete"}</b> — {zh ? "在训练面板中记录收获和下周重点" : "Record lessons and next focus in training panel"}
              </li>
            </ol>
          </div>
        </Section>

        {/* Reference Cases */}
        <Section
          title={zh ? "如何建立参考案例库" : "How to Build a Reference Library"}
          icon="📚"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "参考案例库是你审美训练的「标尺」。建议收集以下三种等级的案例："
                : "The reference case library is your 'yardstick' for aesthetic training. Collect cases at three levels:"}
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <b>{zh ? "高审美（high）" : "High"}</b>: {zh ? "你认为非常优秀的设计，值得学习和借鉴" : "Excellent designs worth learning from"}
              </li>
              <li>
                <b>{zh ? "普通（medium）" : "Medium"}</b>: {zh ? "过得去但不出彩的设计，帮助你建立基准线" : "Decent but unremarkable — helps establish a baseline"}
              </li>
              <li>
                <b>{zh ? "低审美（low）" : "Low"}</b>: {zh ? "有明显问题的设计，帮你训练识别「廉价感」的眼力" : "Designs with obvious problems — trains you to spot 'cheapness'"}
              </li>
            </ul>
            <p>
              {zh
                ? "每个等级建议收集 3-5 个案例。案例越丰富，AI 在做对比分析时越有参考价值。"
                : "Aim for 3-5 cases per level. The richer your library, the more valuable AI's comparison analysis becomes."}
            </p>
          </div>
        </Section>

        {/* Semantic Search & Embedding */}
        <Section
          title={zh ? "语义搜索与 Embedding" : "Semantic Search & Embedding"}
          icon="🔍"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "案例库支持两种搜索方式：普通筛选和语义搜索。"
                : "The case library supports two search modes: regular filters and semantic search."}
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <b>{zh ? "普通筛选" : "Regular filters"}</b>: {zh ? "按分类、审美等级、价格带精确匹配" : "Exact match by category, aesthetic level, price band"}
              </li>
              <li>
                <b>{zh ? "语义搜索" : "Semantic search"}</b>: {zh ? "用自然语言描述你想找的风格，系统按含义匹配。例如输入「高考直播封面，年轻有冲击力但不要廉价」" : "Describe the style you're looking for in natural language — the system matches by meaning"}
              </li>
            </ul>
            <p className="text-xs text-gray-400">
              {zh
                ? "语义搜索需要配置 Embedding（设置页或 .env 中 EMBEDDING_PROVIDER=openai，需要 OpenAI API Key）。配置后在参考案例面板点击「重建索引」。未配置时语义搜索自动降级为普通筛选，不会报错。"
                : "Semantic search requires Embedding (configure EMBEDDING_PROVIDER=openai in Settings or .env, requires OpenAI API Key). After configuring, click 'Rebuild Index' in the Reference Case panel. Falls back to regular filters gracefully when not configured."}
            </p>
          </div>
        </Section>

        {/* Training Assessment */}
        <Section
          title={zh ? "训练效果评估" : "Training Assessment"}
          icon="📊"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "训练评估页面（/assessment）基于历史训练记录进行分析（不依赖 AI，纯规则计算），帮助你了解："
                : "The Assessment page (/assessment) analyzes your training history using rule-based computation (no AI calls), helping you understand:"}
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li>{zh ? "总训练次数、近 7/30 天训练频率" : "Total sessions, recent 7/30 day frequency"}</li>
              <li>{zh ? "你的自评分数 vs AI 评分差距趋势" : "Your self-score vs AI score gap trend"}</li>
              <li>{zh ? "常见误判类型（高估高级感、忽略构图等）" : "Common mistake patterns (overestimating premium feel, ignoring composition, etc.)"}</li>
              <li>{zh ? "7 个审美能力维度的强弱评估" : "7 aesthetic dimension strengths/weaknesses"}</li>
              <li>{zh ? "7/30 天周期复盘与训练建议" : "7/30 day review with training recommendations"}</li>
            </ul>
            <p className="text-xs text-gray-400">
              {zh
                ? "需要至少 5 次包含自评和 AI 评分的训练记录才能生成评估。评估结果是辅助指标，不是绝对评价。"
                : "Requires at least 5 training sessions with both self-scores and AI scores. Results are training aids, not absolute ratings."}
            </p>
          </div>
        </Section>

        {/* System Diagnostics */}
        <Section
          title={zh ? "系统诊断" : "System Diagnostics"}
          icon="🩺"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "设置页顶部的「系统诊断」面板显示 DeepSeek、Vision、Embedding、数据库、上传目录的状态。绿色 ✅ 表示正常，红色 ❌ 表示需要关注。"
                : "The System Diagnostics panel at the top of Settings shows the status of DeepSeek, Vision, Embedding, database, and upload directory. Green ✅ means OK, red ❌ means needs attention."}
            </p>
            <p>
              {zh
                ? "未配置 Key 不代表系统坏了，只是对应功能暂时不可用。面板会给出中文建议告诉你下一步该做什么。"
                : "An unconfigured key doesn't mean the system is broken — that feature is simply unavailable. The panel gives actionable suggestions in Chinese."}
            </p>
          </div>
        </Section>

        {/* Data Export/Import */}
        <Section
          title={zh ? "数据导入/导出" : "Data Import/Export"}
          icon="📦"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "设置页的数据管理区支持导出和导入备份包（.zip）。"
                : "The Data Management area in Settings supports exporting and importing backup packages (.zip)."}
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li><b>{zh ? "导出" : "Export"}</b>: {zh ? "包含参考案例、训练记录、提示词历史、上传的图片、配置摘要。不包含 API Key。" : "Includes reference cases, training records, prompt history, uploaded images, config summary. Does NOT include API keys."}</li>
              <li><b>{zh ? "导入" : "Import"}</b>: {zh ? "合并导入，不会清空或覆盖当前数据。图片和案例 ID 自动重映射。" : "Merge import — never clears or overwrites existing data. Image and case IDs are auto-remapped."}</li>
            </ul>
            <p className="text-xs text-gray-400">
              {zh
                ? "升级前务必导出备份！备份包妥善保存，不要分享给他人。"
                : "Always export a backup before upgrading! Keep the backup file safe and don't share it."}
            </p>
          </div>
        </Section>

        {/* Iteration and Prompts */}
        <Section
          title={zh ? "如何使用迭代与提示词" : "How to Use Iteration & Prompts"}
          icon="🔄"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "「迭代」任务会让 AI 生成 3-5 个具体的设计改版方向，每个方向包含具体建议和预期影响。这适合在你已经分析过一个作品后，想探索不同的改进可能性。"
                : "The 'Iterate' task generates 3-5 specific design alternatives, each with concrete suggestions and expected impact. Use this after analyzing a work to explore improvement possibilities."}
            </p>
            <p>
              {zh
                ? "「生成可复制提示词」功能会把分析结果转化为可用于 Midjourney、DALL·E、Stable Diffusion 等工具的中文/英文提示词、反向提示词和设计说明。适合想快速实践改进方向时使用。"
                : "The 'Generate Prompt' feature converts analysis results into Chinese/English prompts, negative prompts, and design notes for tools like Midjourney, DALL·E, and Stable Diffusion."}
            </p>
          </div>
        </Section>

        {/* History */}
        <Section
          title={zh ? "如何查看历史记录" : "How to View History"}
          icon="📋"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "训练工作台底部的「最近训练记录」列出了你的所有历史训练会话。点击任意一条可以查看完整详情，包括：你的自评、AI 的分析/评分/迭代结果、判断差异对比。"
                : "The 'Recent Sessions' section at the bottom of the workbench lists all your training sessions. Click any entry to view full details including: your self-assessment, AI analysis/critique/iteration results, and judgment gap comparison."}
            </p>
            <p>
              {zh
                ? "训练工作台中间的面板提供统计数据（总次数、本周次数、连续天数、平均分数差距）和每周复盘功能。"
                : "The training panel in the middle of the workbench provides statistics (total sessions, this week, streak, average score gap) and weekly review."}
            </p>
          </div>
        </Section>

        {/* Backup */}
        <Section
          title={zh ? "如何备份数据" : "How to Back Up Data"}
          icon="💾"
        >
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              {zh
                ? "所有数据都在 backend/data/ 目录中。备份方法："
                : "All data is in the backend/data/ directory. To back up:"}
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li>
                {zh
                  ? "直接复制整个 backend/data/ 目录到安全位置"
                  : "Copy the entire backend/data/ directory to a safe location"}
              </li>
              <li>
                {zh
                  ? "database/ 子目录包含 SQLite 数据库（训练记录+案例）"
                  : "The database/ subdirectory contains the SQLite database (training records + cases)"}
              </li>
              <li>
                {zh
                  ? "uploads/ 子目录包含所有上传的图片"
                  : "The uploads/ subdirectory contains all uploaded images"}
              </li>
              <li>
                {zh
                  ? "config/ 子目录包含 API Key 配置（备份时注意安全）"
                  : "The config/ subdirectory contains API key configuration (keep secure when backing up)"}
              </li>
            </ul>
            <p className="text-xs text-gray-400">
              {zh
                ? "建议定期备份。如果使用 Docker，可以在 docker-compose.yml 中挂载 data/ 目录到宿主机。"
                : "Regular backups are recommended. If using Docker, mount the data/ directory to the host in docker-compose.yml."}
            </p>
          </div>
        </Section>

        {/* FAQ */}
        <Section
          title={zh ? "常见问题" : "FAQ"}
          icon="❓"
        >
          <div className="space-y-1">
            {FAQ_ITEMS.map((item, i) => (
              <div key={i} className="rounded border">
                <button
                  onClick={() => toggleFaq(i)}
                  className="w-full px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 flex justify-between items-center"
                >
                  <span>{zh ? item.q.zh : item.q.en}</span>
                  <span className={`text-gray-400 transition-transform ${openFaq === i ? "rotate-180" : ""}`}>
                    ▼
                  </span>
                </button>
                {openFaq === i && (
                  <div className="px-4 pb-3 text-sm text-gray-600 border-t pt-3">
                    {zh ? item.a.zh : item.a.en}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-4 border-t text-center text-xs text-gray-400">
        {zh
          ? "还有问题？可以重新运行首次使用向导，或检查设置页的连接状态。"
          : "Still have questions? Re-run the setup wizard or check connection status on the Settings page."}
      </div>
    </div>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
        <span>{icon}</span> {title}
      </h2>
      {children}
    </section>
  );
}
