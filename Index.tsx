import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  MessageSquareWarning,
  Globe,
  Search,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";

/* ─── Mock backend functions ─── */

const predictMsg = async (text: string): Promise<{ prediction: string; probability: number }> => {
  await new Promise((r) => setTimeout(r, 1500));
  const spamWords = ["free", "win", "prize", "urgent", "click", "claim", "reward", "act now", "limited", "suspended", "verify", "congratulations", "offer", "deal", "cash"];
  const lower = text.toLowerCase();
  const matchCount = spamWords.filter((w) => lower.includes(w)).length;
  const probability = Math.min(0.99, Math.max(0.05, matchCount * 0.18 + Math.random() * 0.1));
  return {
    prediction: probability > 0.5 ? "Spam" : "Not Spam",
    probability: Math.round(probability * 100),
  };
};

const findSpamWords = async (text: string): Promise<string[]> => {
  const spamWords = ["free", "win", "prize", "urgent", "click", "claim", "reward", "act now", "limited", "suspended", "verify", "congratulations", "offer", "deal", "cash", "call"];
  const lower = text.toLowerCase();
  return spamWords.filter((w) => lower.includes(w));
};

const highlightWords = (text: string, words: string[]): string => {
  let result = text;
  words.forEach((word) => {
    const regex = new RegExp(`(${word})`, "gi");
    result = result.replace(regex, `<mark class="bg-danger/30 text-danger px-1 rounded font-semibold">$1</mark>`);
  });
  return result;
};

type UrlStatus = "SAFE" | "SUSPICIOUS" | "HIGH RISK";

const checkUrlSafety = async (url: string): Promise<{ status: UrlStatus; score: number; reasons: string[] }> => {
  await new Promise((r) => setTimeout(r, 1800));
  const lower = url.toLowerCase();
  const redFlags = [
    { pattern: /\.tk|\.ml|\.ga|\.cf|\.gq/, reason: "Uses free/suspicious top-level domain" },
    { pattern: /paypa1|g00gle|amaz0n|faceb00k/, reason: "Domain mimics a well-known brand (typosquatting)" },
    { pattern: /verify|account|security|login|confirm/, reason: "Contains phishing-related keywords" },
    { pattern: /free|prize|winner|claim|reward/, reason: "Contains social engineering keywords" },
    { pattern: /^http:\/\//, reason: "Uses insecure HTTP connection (no SSL)" },
    { pattern: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/, reason: "Uses raw IP address instead of domain" },
    { pattern: /@/, reason: "Contains @ symbol (possible URL obfuscation)" },
  ];
  const matched = redFlags.filter((f) => f.pattern.test(lower));
  const score = Math.min(100, matched.length * 22 + Math.floor(Math.random() * 10));
  const status: UrlStatus = score >= 60 ? "HIGH RISK" : score >= 30 ? "SUSPICIOUS" : "SAFE";
  const reasons = matched.length > 0 ? matched.map((m) => m.reason) : ["No known threats detected", "Domain appears legitimate", "SSL certificate present"];
  return { status, score, reasons };
};

/* ─── Constants ─── */

const SAMPLE_MESSAGES = [
  { label: "Spam SMS", text: "URGENT! You have won a £1,000 prize! Call 0800-123-456 NOW to claim your FREE reward. Reply STOP to opt out." },
  { label: "Legit Email", text: "Hi Sarah, just wanted to confirm our meeting tomorrow at 3 PM in the conference room. Let me know if that still works for you." },
  { label: "Phishing", text: "Your PayPal account has been limited. Click here to verify your identity immediately or your account will be suspended. Act now!" },
];

const SAMPLE_URLS = [
  { label: "Safe", url: "https://www.google.com" },
  { label: "Suspicious", url: "http://free-prizes-winner.xyz/claim" },
  { label: "Dangerous", url: "http://paypa1-security.tk/verify-account" },
];

type Tab = "spam" | "url";

const tabs: { id: Tab; label: string; icon: typeof MessageSquareWarning }[] = [
  { id: "spam", label: "Spam Detection", icon: MessageSquareWarning },
  { id: "url", label: "URL Safety Checker", icon: Globe },
];

const urlStatusConfig: Record<UrlStatus, { color: string; bg: string; border: string; glow: string; Icon: typeof ShieldCheck }> = {
  SAFE: { color: "text-safe", bg: "bg-safe/5", border: "border-safe/40", glow: "cyber-glow-safe", Icon: ShieldCheck },
  SUSPICIOUS: { color: "text-warning", bg: "bg-warning/5", border: "border-warning/40", glow: "", Icon: AlertTriangle },
  "HIGH RISK": { color: "text-danger", bg: "bg-danger/5", border: "border-danger/40", glow: "cyber-glow-danger", Icon: ShieldAlert },
};

/* ─── Header ─── */

const Header = () => (
  <motion.header
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6 }}
    className="text-center py-10"
  >
    <div className="flex items-center justify-center gap-3 mb-3">
      <div className="relative">
        <Shield className="w-10 h-10 text-primary" />
        <div className="absolute inset-0 w-10 h-10 text-primary blur-lg opacity-50">
          <Shield className="w-10 h-10" />
        </div>
      </div>
      <h1 className="text-4xl md:text-5xl font-bold font-mono tracking-tight text-gradient-cyber">
        Spam Shield
      </h1>
    </div>
    <p className="text-muted-foreground text-lg font-light tracking-wide">
      AI-Based Message & URL Security System
    </p>
    <div className="mt-6 h-px w-full max-w-md mx-auto bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
  </motion.header>
);

/* ─── Spam Detection ─── */

const SpamDetection = () => {
  const [message, setMessage] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<{
    prediction: string;
    probability: number;
    highlightedText: string;
    suspiciousWords: string[];
  } | null>(null);

  const handleAnalyze = async () => {
    if (!message.trim()) return;
    setAnalyzing(true);
    setResult(null);
    const [predResult, words] = await Promise.all([predictMsg(message), findSpamWords(message)]);
    const highlighted = highlightWords(message, words);
    setResult({ prediction: predResult.prediction, probability: predResult.probability, highlightedText: highlighted, suspiciousWords: words });
    setAnalyzing(false);
  };

  const isSpam = result?.prediction === "Spam";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground mr-1 self-center">Try:</span>
        {SAMPLE_MESSAGES.map((s) => (
          <Button key={s.label} variant="outline" size="sm" className="text-xs border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all" onClick={() => { setMessage(s.text); setResult(null); }}>
            <Sparkles className="w-3 h-3 mr-1" />
            {s.label}
          </Button>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-5 space-y-4">
        <Textarea placeholder="Paste a suspicious SMS or email message here..." className="min-h-[140px] bg-secondary/50 border-border/50 font-mono text-sm resize-none focus:border-primary/50 transition-colors" value={message} onChange={(e) => { setMessage(e.target.value); setResult(null); }} />
        <Button className="w-full gap-2 font-semibold" onClick={handleAnalyze} disabled={!message.trim() || analyzing}>
          {analyzing ? (
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
              <Search className="w-4 h-4" />
            </motion.div>
          ) : (
            <Search className="w-4 h-4" />
          )}
          {analyzing ? "Analyzing..." : "Analyze Message"}
        </Button>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.4 }} className="space-y-4">
            <div className={`rounded-lg border p-5 ${isSpam ? "border-danger/40 bg-danger/5 cyber-glow-danger" : "border-safe/40 bg-safe/5 cyber-glow-safe"}`}>
              <div className="flex items-center gap-3 mb-4">
                {isSpam ? <ShieldAlert className="w-8 h-8 text-danger" /> : <ShieldCheck className="w-8 h-8 text-safe" />}
                <div>
                  <p className={`text-2xl font-bold font-mono ${isSpam ? "text-danger" : "text-safe"}`}>{result.prediction}</p>
                  <p className="text-sm text-muted-foreground">Confidence: {result.probability}%</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Risk Level</span>
                  <span>{result.probability}%</span>
                </div>
                <div className="relative h-3 rounded-full bg-secondary overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${result.probability}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className={`absolute inset-y-0 left-0 rounded-full ${result.probability > 70 ? "bg-danger" : result.probability > 40 ? "bg-warning" : "bg-safe"}`} />
                </div>
              </div>
            </div>

            {result.suspiciousWords.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-warning" />
                  <h3 className="font-semibold text-sm">Suspicious Words Detected</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.suspiciousWords.map((word) => (
                    <span key={word} className="px-2 py-1 rounded text-xs font-mono bg-danger/10 text-danger border border-danger/20">{word}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg border border-border bg-card p-5 space-y-3">
              <h3 className="font-semibold text-sm">Message Analysis</h3>
              <div className="text-sm font-mono leading-relaxed text-secondary-foreground" dangerouslySetInnerHTML={{ __html: result.highlightedText }} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/* ─── URL Checker ─── */

const UrlChecker = () => {
  const [url, setUrl] = useState("");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<{ status: UrlStatus; score: number; reasons: string[] } | null>(null);

  const handleScan = async () => {
    if (!url.trim()) return;
    setScanning(true);
    setResult(null);
    const res = await checkUrlSafety(url);
    setResult(res);
    setScanning(false);
  };

  const cfg = result ? urlStatusConfig[result.status] : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground mr-1 self-center">Try:</span>
        {SAMPLE_URLS.map((s) => (
          <Button key={s.label} variant="outline" size="sm" className="text-xs border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all" onClick={() => { setUrl(s.url); setResult(null); }}>
            <Sparkles className="w-3 h-3 mr-1" />
            {s.label}
          </Button>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-5 space-y-4">
        <div className="relative">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="https://example.com" className="pl-10 bg-secondary/50 border-border/50 font-mono text-sm focus:border-primary/50 transition-colors" value={url} onChange={(e) => { setUrl(e.target.value); setResult(null); }} onKeyDown={(e) => e.key === "Enter" && handleScan()} />
        </div>
        <Button className="w-full gap-2 font-semibold" onClick={handleScan} disabled={!url.trim() || scanning}>
          {scanning ? (
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
              <Search className="w-4 h-4" />
            </motion.div>
          ) : (
            <Search className="w-4 h-4" />
          )}
          {scanning ? "Scanning..." : "Scan URL"}
        </Button>
      </div>

      <AnimatePresence>
        {scanning && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="rounded-lg border border-primary/20 bg-card p-6 relative overflow-hidden">
            <div className="scan-line absolute inset-0 h-full" />
            <div className="text-center space-y-2">
              <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 1.5 }} className="inline-block">
                <Globe className="w-8 h-8 text-primary mx-auto" />
              </motion.div>
              <p className="text-sm font-mono text-muted-foreground">Scanning URL for threats...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {result && cfg && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }} className="space-y-4">
            <div className={`rounded-lg border p-5 ${cfg.bg} ${cfg.border} ${cfg.glow}`}>
              <div className="flex items-center gap-3 mb-4">
                <cfg.Icon className={`w-8 h-8 ${cfg.color}`} />
                <div>
                  <p className={`text-2xl font-bold font-mono ${cfg.color}`}>{result.status}</p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate max-w-xs">{url}</span>
                  </p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Risk Score</span>
                  <span>{result.score}/100</span>
                </div>
                <div className="relative h-3 rounded-full bg-secondary overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${result.score}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className={`absolute inset-y-0 left-0 rounded-full ${result.score >= 60 ? "bg-danger" : result.score >= 30 ? "bg-warning" : "bg-safe"}`} />
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-border bg-card p-5 space-y-3">
              <h3 className="font-semibold text-sm">Analysis Details</h3>
              <ul className="space-y-2">
                {result.reasons.map((reason, i) => (
                  <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="flex items-start gap-2 text-sm">
                    <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${result.status === "SAFE" ? "bg-safe" : result.status === "SUSPICIOUS" ? "bg-warning" : "bg-danger"}`} />
                    <span className="text-secondary-foreground">{reason}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/* ─── Main Page ─── */

const Index = () => {
  const [activeTab, setActiveTab] = useState<Tab>("spam");

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(hsl(173 80% 40%) 1px, transparent 1px), linear-gradient(90deg, hsl(173 80% 40%) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />

      <div className="relative z-10 max-w-2xl mx-auto px-4 pb-16">
        <Header />

        <div className="flex gap-1 p-1 rounded-lg bg-secondary/50 border border-border/50 mb-8">
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`relative flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
              {activeTab === tab.id && (
                <motion.div layoutId="activeTab" className="absolute inset-0 bg-primary rounded-md" transition={{ type: "spring", duration: 0.4, bounce: 0.15 }} />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </span>
            </button>
          ))}
        </div>

        <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          {activeTab === "spam" ? <SpamDetection /> : <UrlChecker />}
        </motion.div>
      </div>
    </div>
  );
};

export default Index;
