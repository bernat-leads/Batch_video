import { useEffect, useState } from "react";
import { clsx } from "keycloakify/tools/clsx";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { useSetClassName } from "keycloakify/tools/useSetClassName";
import { useInitialize } from "keycloakify/login/Template.useInitialize";
import type { I18n } from "./i18n";
import type { KcContext } from "./KcContext";
import { Button } from "@packages/ui/components/shadcn/button";
import { Card } from "@packages/ui/components/shadcn/card";
import { ChevronDown, AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";

export default function Template(props: TemplateProps<KcContext, I18n>) {
    const {
        displayInfo = false,
        displayMessage = true,
        displayRequiredFields = false,
        headerNode,
        socialProvidersNode = null,
        infoNode = null,
        documentTitle,
        bodyClassName,
        kcContext,
        i18n,
        doUseDefaultCss,
        classes,
        children
    } = props;

    const { kcClsx } = getKcClsx({ doUseDefaultCss, classes });

    const { msg, msgStr, currentLanguage, enabledLanguages } = i18n;

    const { realm, auth, url, message, isAppInitiatedAction } = kcContext;

    const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);

    useEffect(() => {
        document.title = documentTitle ?? msgStr("loginTitle", realm.displayName);
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as Element;
            if (!target.closest("[data-language-dropdown]")) {
                setIsLanguageDropdownOpen(false);
            }
        };

        if (isLanguageDropdownOpen) {
            document.addEventListener("mousedown", handleClickOutside);
            return () => document.removeEventListener("mousedown", handleClickOutside);
        }
    }, [isLanguageDropdownOpen]);

    useSetClassName({
        qualifiedName: "html",
        className: kcClsx("kcHtmlClass")
    });

    useSetClassName({
        qualifiedName: "body",
        className: bodyClassName ?? kcClsx("kcBodyClass")
    });

    const { isReadyToRender } = useInitialize({ kcContext, doUseDefaultCss });

    if (!isReadyToRender) {
        return null;
    }

    const getMessageIcon = (type: string) => {
        switch (type) {
            case "success":
                return <CheckCircle className="h-4 w-4" />;
            case "warning":
                return <AlertTriangle className="h-4 w-4" />;
            case "error":
                return <AlertCircle className="h-4 w-4" />;
            case "info":
                return <Info className="h-4 w-4" />;
            default:
                return <Info className="h-4 w-4" />;
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="w-full max-w-md space-y-6">
                {/* Language Selector */}
                {enabledLanguages.length > 1 && (
                    <div className="flex justify-end">
                        <div className="relative" data-language-dropdown>
                            <Button
                                tabIndex={1}
                                id="kc-current-locale-link"
                                variant="outline"
                                size="sm"
                                aria-label={msgStr("languages")}
                                aria-haspopup="true"
                                aria-expanded={isLanguageDropdownOpen}
                                aria-controls="language-switch1"
                                onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
                                className="bg-white border-gray-300 text-gray-900 hover:bg-gray-50"
                            >
                                {currentLanguage.label}
                                <ChevronDown className="ml-2 h-4 w-4" />
                            </Button>
                            {isLanguageDropdownOpen && (
                                <Card className="absolute right-0 mt-2 w-56 border-gray-200 shadow-md z-10">
                                    <div
                                        role="menu"
                                        tabIndex={-1}
                                        aria-labelledby="kc-current-locale-link"
                                        aria-activedescendant=""
                                        id="language-switch1"
                                        className="p-1"
                                    >
                                        {enabledLanguages.map(({ languageTag, label, href }, i) => (
                                            <div key={languageTag} role="none">
                                                <a
                                                    role="menuitem"
                                                    id={`language-${i + 1}`}
                                                    href={href}
                                                    className="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-sm"
                                                    onClick={() => setIsLanguageDropdownOpen(false)}
                                                >
                                                    {label}
                                                </a>
                                            </div>
                                        ))}
                                    </div>
                                </Card>
                            )}
                        </div>
                    </div>
                )}

                {/* Page Title */}
                {headerNode && (
                    <div className="text-center">
                        {(() => {
                            const node = !(auth !== undefined && auth.showUsername && !auth.showResetCredentials) ? (
                                <div>{headerNode}</div>
                            ) : (
                                <Card className="bg-white border-gray-200 p-4">
                                    <div className="text-center space-y-2">
                                        <p className="text-sm text-gray-600">
                                            Logging in as: <span className="font-medium text-gray-900">{auth.attemptedUsername}</span>
                                        </p>
                                        <Button id="reset-login" variant="link" className="h-auto p-0 text-sm font-normal" asChild>
                                            <a href={url.loginRestartFlowUrl} aria-label={msgStr("restartLoginTooltip")}>
                                                {msg("restartLoginTooltip")}
                                            </a>
                                        </Button>
                                    </div>
                                </Card>
                            );

                            if (displayRequiredFields) {
                                return (
                                    <div className="space-y-4">
                                        <div className="text-center">
                                            <span className="text-sm text-gray-600">
                                                <span className="text-red-600">*</span> {msg("requiredFields")}
                                            </span>
                                        </div>
                                        {node}
                                    </div>
                                );
                            }

                            return node;
                        })()}
                    </div>
                )}

                {/* Messages */}
                {displayMessage && message !== undefined && (message.type !== "warning" || !isAppInitiatedAction) && (
                    <Card
                        className={clsx(
                            "border p-4",
                            message.type === "success" && "border-green-200 bg-green-50",
                            message.type === "warning" && "border-yellow-200 bg-yellow-50",
                            message.type === "error" && "border-red-200 bg-red-50",
                            message.type === "info" && "border-blue-200 bg-blue-50"
                        )}
                    >
                        <div className="flex items-start space-x-3">
                            <div
                                className={clsx(
                                    "flex-shrink-0 mt-0.5",
                                    message.type === "success" && "text-green-600",
                                    message.type === "warning" && "text-yellow-600",
                                    message.type === "error" && "text-red-600",
                                    message.type === "info" && "text-blue-600"
                                )}
                            >
                                {getMessageIcon(message.type)}
                            </div>
                            <div className="flex-1">
                                <p
                                    className={clsx(
                                        "text-sm font-medium",
                                        message.type === "success" && "text-green-800",
                                        message.type === "warning" && "text-yellow-800",
                                        message.type === "error" && "text-red-800",
                                        message.type === "info" && "text-blue-800"
                                    )}
                                    dangerouslySetInnerHTML={{
                                        __html: kcSanitize(message.summary)
                                    }}
                                />
                            </div>
                        </div>
                    </Card>
                )}

                {/* Main Content */}
                <div className="space-y-6">
                    {children}

                    {/* Try Another Way */}
                    {auth !== undefined && auth.showTryAnotherWayLink && (
                        <div className="text-center">
                            <Button
                                variant="link"
                                className="h-auto p-0 text-sm font-normal"
                                onClick={() => {
                                    document.forms["kc-select-try-another-way-form" as never].requestSubmit();
                                }}
                            >
                                {msg("doTryAnotherWay")}
                            </Button>
                            <form id="kc-select-try-another-way-form" action={url.loginAction} method="post" className="hidden">
                                <input type="hidden" name="tryAnotherWay" value="on" />
                            </form>
                        </div>
                    )}

                    {/* Social Providers */}
                    {socialProvidersNode}

                    {/* Info Section */}
                    {displayInfo && infoNode && <div className="border-t border-gray-200 pt-6">{infoNode}</div>}
                </div>
            </div>
        </div>
    );
}
