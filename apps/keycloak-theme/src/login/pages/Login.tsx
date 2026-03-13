import type { JSX } from "keycloakify/tools/JSX";
import { useState } from "react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { useIsPasswordRevealed } from "keycloakify/tools/useIsPasswordRevealed";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import type { KcClsx } from "keycloakify/login/lib/kcClsx";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import { Eye, EyeOff, Lock, Mail, User, Chrome, Github, Facebook } from "lucide-react";
import { Button } from "@packages/ui/components/shadcn/button";
import { Input } from "@packages/ui/components/shadcn/input";
import { Label } from "@packages/ui/components/shadcn/label";
import { Card, CardContent, CardHeader } from "@packages/ui/components/shadcn/card";
import { Checkbox } from "@packages/ui/components/shadcn/checkbox";
import { Separator } from "@packages/ui/components/shadcn/separator";

export default function Login(props: PageProps<Extract<KcContext, { pageId: "login.ftl" }>, I18n>) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

    const { kcClsx } = getKcClsx({
        doUseDefaultCss,
        classes
    });

    const { social, realm, url, usernameHidden, login, auth, registrationDisabled, messagesPerField } = kcContext;

    const { msg, msgStr } = i18n;

    const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

    const getSocialIcon = (providerId: string) => {
        switch (providerId.toLowerCase()) {
            case "google":
                return <Chrome className="h-4 w-4" />;
            case "github":
                return <Github className="h-4 w-4" />;
            case "facebook":
                return <Facebook className="h-4 w-4" />;
            default:
                return null;
        }
    };

    return (
        <Template
            kcContext={kcContext}
            i18n={i18n}
            doUseDefaultCss={doUseDefaultCss}
            classes={classes}
            displayMessage={!messagesPerField.existsError("username", "password")}
            headerNode={null}
            displayInfo={realm.password && realm.registrationAllowed && !registrationDisabled}
            infoNode={
                <div className="text-center text-sm text-gray-600">
                    Don&apos;t have an account?{" "}
                    <Button variant="link" className="h-auto p-0 text-sm font-normal" asChild>
                        <a href={url.registrationUrl}>Sign up</a>
                    </Button>
                </div>
            }
            socialProvidersNode={
                <>
                    {realm.password && social?.providers !== undefined && social.providers.length !== 0 && (
                        <div className="space-y-4">
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <Separator className="w-full" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-white px-2 text-gray-500">Or continue with</span>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-2">
                                {social.providers.map(p => (
                                    <Button
                                        key={p.alias}
                                        id={`social-${p.alias}`}
                                        variant="outline"
                                        className="w-full bg-white border-gray-300 text-gray-900 hover:bg-gray-50"
                                        asChild
                                    >
                                        <a href={p.loginUrl} className="flex items-center justify-center gap-2">
                                            {getSocialIcon(p.alias)}
                                            <span dangerouslySetInnerHTML={{ __html: kcSanitize(p.displayName) }} />
                                        </a>
                                    </Button>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            }
        >
            <Card className="bg-white border-gray-200 shadow-sm pb-6">
                <CardHeader className="space-y-1 flex flex-col items-center pb-0">
                    <h1 className="text-2xl font-semibold text-gray-900 tracking-tight text-center">{msg("loginAccountTitle")}</h1>
                    <p className="text-sm text-gray-600 mt-2 text-center">Enter your credentials below to access your account</p>
                </CardHeader>
                <CardContent className="pb-6">
                    {realm.password && (
                        <form
                            id="kc-form-login"
                            onSubmit={() => {
                                setIsLoginButtonDisabled(true);
                                return true;
                            }}
                            action={url.loginAction}
                            method="post"
                        >
                            <div className="grid gap-4">
                                {!usernameHidden && (
                                    <div className="grid gap-2">
                                        <Label htmlFor="username" className="text-sm font-medium text-gray-900">
                                            {!realm.loginWithEmailAllowed
                                                ? msg("username")
                                                : !realm.registrationEmailAsUsername
                                                  ? msg("usernameOrEmail")
                                                  : msg("email")}
                                        </Label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                {realm.loginWithEmailAllowed ? (
                                                    <Mail className="h-4 w-4 text-gray-400" />
                                                ) : (
                                                    <User className="h-4 w-4 text-gray-400" />
                                                )}
                                            </div>
                                            <Input
                                                tabIndex={2}
                                                id="username"
                                                name="username"
                                                defaultValue={login.username ?? ""}
                                                type="text"
                                                autoFocus
                                                autoComplete="username"
                                                aria-invalid={messagesPerField.existsError("username", "password")}
                                                className="pl-10 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-gray-400 focus:ring-0"
                                                placeholder={msgStr(
                                                    !realm.loginWithEmailAllowed
                                                        ? "username"
                                                        : !realm.registrationEmailAsUsername
                                                          ? "usernameOrEmail"
                                                          : "email"
                                                )}
                                                required
                                            />
                                        </div>
                                        {messagesPerField.existsError("username", "password") && (
                                            <p className="text-sm text-red-600" aria-live="polite">
                                                {messagesPerField.getFirstError("username", "password")}
                                            </p>
                                        )}
                                    </div>
                                )}

                                <div className="grid gap-2">
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="password" className="text-sm font-medium text-gray-900">
                                            {msg("password")}
                                        </Label>
                                        {realm.resetPasswordAllowed && (
                                            <Button variant="link" className="h-auto p-0 text-sm font-normal" asChild>
                                                <a href={url.loginResetCredentialsUrl}>Forgot your password?</a>
                                            </Button>
                                        )}
                                    </div>
                                    <PasswordWrapper kcClsx={kcClsx} i18n={i18n} passwordInputId="password">
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                <Lock className="h-4 w-4 text-gray-400" />
                                            </div>
                                            <Input
                                                tabIndex={3}
                                                id="password"
                                                name="password"
                                                type="password"
                                                autoComplete="current-password"
                                                aria-invalid={messagesPerField.existsError("username", "password")}
                                                className="pl-10 pr-10 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-gray-400 focus:ring-0"
                                                placeholder={msgStr("password")}
                                                required
                                            />
                                        </div>
                                    </PasswordWrapper>
                                    {usernameHidden && messagesPerField.existsError("username", "password") && (
                                        <p className="text-sm text-red-600" aria-live="polite">
                                            {messagesPerField.getFirstError("username", "password")}
                                        </p>
                                    )}
                                </div>

                                {realm.rememberMe && !usernameHidden && (
                                    <div className="flex items-center gap-3">
                                        <Checkbox
                                            tabIndex={5}
                                            id="rememberMe"
                                            name="rememberMe"
                                            defaultChecked={!!login.rememberMe}
                                            className="border-gray-300 data-[state=checked]:bg-white data-[state=checked]:border-gray-400 focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
                                        />
                                        <Label htmlFor="rememberMe" className="text-sm font-normal text-gray-700 mt-0.5">
                                            {msg("rememberMe")}
                                        </Label>
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <input type="hidden" id="id-hidden-input" name="credentialId" value={auth.selectedCredential} />
                                    <Button
                                        tabIndex={7}
                                        disabled={isLoginButtonDisabled}
                                        type="submit"
                                        className="w-full bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
                                    >
                                        {isLoginButtonDisabled ? (
                                            <>
                                                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                                Signing in...
                                            </>
                                        ) : (
                                            msgStr("doLogIn")
                                        )}
                                    </Button>
                                </div>
                            </div>
                        </form>
                    )}
                </CardContent>
            </Card>
        </Template>
    );
}

function PasswordWrapper(props: { kcClsx: KcClsx; i18n: I18n; passwordInputId: string; children: JSX.Element }) {
    const { i18n, passwordInputId, children } = props;

    const { msgStr } = i18n;

    const { isPasswordRevealed, toggleIsPasswordRevealed } = useIsPasswordRevealed({ passwordInputId });

    return (
        <div className="relative">
            {children}
            <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute inset-y-0 right-0 pr-3 h-auto hover:bg-transparent text-gray-400 hover:text-gray-600"
                aria-label={msgStr(isPasswordRevealed ? "hidePassword" : "showPassword")}
                aria-controls={passwordInputId}
                onClick={toggleIsPasswordRevealed}
            >
                {isPasswordRevealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
        </div>
    );
}
