"""Domain-partitioned service exports: _integration_and_io."""
from __future__ import annotations

from harness.services.notification import (
    NOTIFICATION_SERVICE_KEY,
    NotificationService,
    TaskEventResult,
    WebhookDeliveryResult,
)

from harness.services.openapi import (
    OPENAPI_SPEC_KEY,
    OpenApiMockResult,
    OpenApiSpecResult,
    OpenApiSpecService,
    OpenApiValidationResult,
)

from harness.services.openrouter_gateway import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterChatResponse,
    OpenRouterGatewayService,
    OpenRouterModelInfo,
    RouteResolution,
)

from harness.services.stagehand_browser import (
    STAGEHAND_BROWSER_KEY,
    StagehandBrowserService,
)

from harness.services.web_fetcher import (
    WEB_FETCHER_KEY,
    WebFetcherService,
    WebFetchResult,
    WebHttpResponse,
    WebMarkdownResult,
)

from harness.services.chatbotx import (
    CHATBOTX_SERVICE_KEY,
    ChatbotXConfig,
    ChatbotXService,
    ContactRecord,
    ConversationSummary,
    DefaultChatbotXService,
    FlowExecution,
    MessageRecord,
    ToolResult,
)

from harness.services.gemini_vercel import (
    GEMINI_VERCEL_STREAMING_SERVICE_KEY,
    AuditCheckData,
    AuditReportData,
    GeminiVercelStreamingService,
    ScaffoldConfigData,
    ScaffoldResultData,
    StreamSimulationData,
)

from harness.services.gradio_app import (
    GRADIO_APP_ARCHITECT_SERVICE_KEY,
    AppScaffoldConfigData,
    AppScaffoldResultData,
    DiagnosticCheckData,
    DiagnosticReportData,
    GradioAppArchitectService,
)
