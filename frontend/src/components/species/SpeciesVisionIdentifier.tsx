import React, { useState, useRef, useEffect } from 'react';
import { speciesService } from '../../services/species';
import { 
  SpeciesIdentificationResponse, 
  SpeciesModelInfoResponse 
} from '../../types/species';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { 
  Camera, 
  UploadCloud, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle,
  ExternalLink, 
  RefreshCw, 
  Cpu, 
  Info, 
  Layers,
  Fish,
  Sliders,
  X
} from 'lucide-react';

// Generates an in-memory sample fish canvas dataURL for instant testing
function createSampleFishBlob(speciesName: string): Promise<File> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    canvas.width = 224;
    canvas.height = 224;
    const ctx = canvas.getContext('2d')!;

    // Underwater ocean gradient background
    const bgGrad = ctx.createLinearGradient(0, 0, 0, 224);
    bgGrad.addColorStop(0, '#0c2e4e');
    bgGrad.addColorStop(1, '#051829');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 224, 224);

    // Subtle reef texture
    ctx.fillStyle = '#0f384a';
    ctx.beginPath();
    ctx.arc(40, 200, 50, 0, Math.PI * 2);
    ctx.arc(180, 210, 60, 0, Math.PI * 2);
    ctx.fill();

    // Stylized fish silhouette with characteristic coloration
    ctx.save();
    ctx.translate(112, 112);

    let bodyColor = '#f59e0b';
    let stripeColor = '#ffffff';

    if (speciesName.includes('Amphiprion')) {
      // Clownfish: Orange with white stripes
      bodyColor = '#ea580c';
      stripeColor = '#ffffff';
    } else if (speciesName.includes('Chaetodon')) {
      // Butterflyfish: Yellow/lemon with dark chevron
      bodyColor = '#eab308';
      stripeColor = '#1e293b';
    } else if (speciesName.includes('Lutjanus')) {
      // Snapper: Red/copper
      bodyColor = '#dc2626';
      stripeColor = '#fca5a5';
    } else if (speciesName.includes('Canthigaster')) {
      // Puffer: White/tan with dark spots
      bodyColor = '#d97706';
      stripeColor = '#fef3c7';
    } else {
      bodyColor = '#06b6d4';
      stripeColor = '#0e7490';
    }

    // Fish body oval
    ctx.fillStyle = bodyColor;
    ctx.beginPath();
    ctx.ellipse(0, 0, 55, 32, 0, 0, Math.PI * 2);
    ctx.fill();

    // Caudal fin (tail)
    ctx.beginPath();
    ctx.moveTo(-45, 0);
    ctx.lineTo(-75, -25);
    ctx.lineTo(-65, 0);
    ctx.lineTo(-75, 25);
    ctx.closePath();
    ctx.fillStyle = bodyColor;
    ctx.fill();

    // Dorsal fin
    ctx.beginPath();
    ctx.moveTo(-20, -28);
    ctx.quadraticCurveTo(0, -45, 25, -26);
    ctx.closePath();
    ctx.fillStyle = bodyColor;
    ctx.fill();

    // Distinctive stripes/bars
    ctx.strokeStyle = stripeColor;
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(10, -28);
    ctx.lineTo(10, 28);
    ctx.moveTo(-15, -24);
    ctx.lineTo(-15, 24);
    ctx.stroke();

    // Eye
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(32, -8, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#0f172a';
    ctx.beginPath();
    ctx.arc(34, -8, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `${speciesName.replace(/\s+/g, '_')}_sample.jpg`, {
          type: 'image/jpeg'
        });
        resolve(file);
      }
    }, 'image/jpeg', 0.95);
  });
}

export const SpeciesVisionIdentifier: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [topK, setTopK] = useState<number>(3);
  const [isClassifying, setIsClassifying] = useState<boolean>(false);
  const [result, setResult] = useState<SpeciesIdentificationResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<SpeciesModelInfoResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isCatalogModalOpen, setIsCatalogModalOpen] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch model catalog on mount
  useEffect(() => {
    speciesService.getSpeciesModelInfo()
      .then(setModelInfo)
      .catch((err) => console.warn('Could not load species vision model metadata:', err));
  }, []);

  const handleFileChange = (file: File) => {
    setErrorMsg(null);
    setResult(null);

    // Validate image MIME / extension
    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please select a valid image file (JPEG, PNG, or WebP).');
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setErrorMsg('Image file size exceeds the 20MB limit.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSampleClick = async (speciesName: string) => {
    try {
      const file = await createSampleFishBlob(speciesName);
      handleFileChange(file);
    } catch (err: any) {
      setErrorMsg('Failed to generate sample fish test image.');
    }
  };

  const handleClassify = async () => {
    if (!selectedFile) return;

    setIsClassifying(true);
    setErrorMsg(null);

    try {
      const prediction = await speciesService.identifySpecies(selectedFile, topK);
      setResult(prediction);
    } catch (err: any) {
      console.error('Classification error:', err);
      setErrorMsg(err.message || 'Classification failed. Please check the backend connection.');
    } finally {
      setIsClassifying(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setResult(null);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'HIGH':
        return <Badge variant="teal" size="sm" dot>HIGH CONFIDENCE (≥70%)</Badge>;
      case 'MODERATE':
        return <Badge variant="amber" size="sm" dot>MODERATE CONFIDENCE (40–70%)</Badge>;
      default:
        return <Badge variant="coral" size="sm" dot>LOW CONFIDENCE (&lt;40%)</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Component Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-marine-900 via-marine-950 to-marine-900 border border-marine-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-ocean-cyan/10 border border-ocean-cyan/20 text-ocean-cyan">
              <Camera className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Deep Learning Visual Species Identification
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-ocean-cyan/20 text-ocean-cyan border border-ocean-cyan/30 font-mono">
                  Phase 14.2
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                ResNet-18 Computer Vision inference calibrated on 10 Western Indian Ocean & Arabian Sea fish species.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            leftIcon={<Layers className="w-3.5 h-3.5 text-ocean-cyan" />}
            onClick={() => setIsCatalogModalOpen(true)}
          >
            10 Supported Species
          </Button>
          <Badge variant="cyan" size="sm">
            ResNet-18 v1.0.0
          </Badge>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Upload & Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-5 border-marine-800 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <UploadCloud className="w-4 h-4 text-ocean-cyan" />
                Input Image / Camera Frame
              </h4>
              {previewUrl && (
                <button
                  onClick={handleReset}
                  className="text-xs text-slate-400 hover:text-ocean-coral flex items-center gap-1 transition-colors"
                  title="Remove image"
                >
                  <X className="w-3.5 h-3.5" /> Clear
                </button>
              )}
            </div>

            {/* Hidden File Input */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/jpeg,image/png,image/webp,image/bmp"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />

            {/* Dropzone / Preview Area */}
            {!previewUrl ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                  isDragOver 
                    ? 'border-ocean-cyan bg-ocean-cyan/10 scale-[1.01]' 
                    : 'border-marine-700 bg-marine-950/60 hover:border-ocean-cyan/50 hover:bg-marine-900/50'
                }`}
              >
                <div className="w-12 h-12 rounded-full bg-marine-800/80 border border-marine-700 mx-auto flex items-center justify-center text-ocean-cyan mb-3">
                  <Camera className="w-6 h-6" />
                </div>
                <p className="text-xs font-semibold text-white">
                  Drop underwater photograph here
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  or click to browse local files (JPEG, PNG, WebP)
                </p>
                <span className="inline-block mt-3 px-2 py-0.5 rounded bg-marine-900 border border-marine-800 text-[10px] font-mono text-slate-400">
                  Target Resolution: 224 × 224 RGB
                </span>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="relative rounded-xl overflow-hidden border border-marine-750 bg-black/40 aspect-square max-h-[300px] flex items-center justify-center group">
                  <img
                    src={previewUrl}
                    alt="Target Marine Fish Preview"
                    className="w-full h-full object-contain"
                  />
                  {isClassifying && (
                    <div className="absolute inset-0 bg-marine-950/80 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
                      <div className="w-10 h-10 border-2 border-ocean-cyan border-t-transparent rounded-full animate-spin" />
                      <p className="text-xs font-mono text-ocean-cyan animate-pulse">
                        Classifying with ResNet-18...
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
                  <span className="truncate max-w-[200px]" title={selectedFile?.name}>
                    {selectedFile?.name}
                  </span>
                  <span>
                    {selectedFile ? (selectedFile.size / 1024).toFixed(1) : 0} KB
                  </span>
                </div>
              </div>
            )}

            {/* Quick Test Presets */}
            <div className="space-y-2 pt-2 border-t border-marine-850">
              <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-ocean-cyan" />
                Quick Test Samples:
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => handleSampleClick('Amphiprion clarkii')}
                  className="px-2.5 py-1.5 rounded-lg bg-marine-950 border border-marine-800 hover:border-ocean-cyan/40 text-left text-slate-300 hover:text-white transition-colors"
                >
                  <span className="block font-semibold text-[11px] text-amber-400">A. clarkii</span>
                  <span className="text-[10px] text-slate-400">Yellowtail clownfish</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSampleClick('Chaetodon lunulatus')}
                  className="px-2.5 py-1.5 rounded-lg bg-marine-950 border border-marine-800 hover:border-ocean-cyan/40 text-left text-slate-300 hover:text-white transition-colors"
                >
                  <span className="block font-semibold text-[11px] text-yellow-300">C. lunulatus</span>
                  <span className="text-[10px] text-slate-400">Oval butterflyfish</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSampleClick('Lutjanus fulvus')}
                  className="px-2.5 py-1.5 rounded-lg bg-marine-950 border border-marine-800 hover:border-ocean-cyan/40 text-left text-slate-300 hover:text-white transition-colors"
                >
                  <span className="block font-semibold text-[11px] text-rose-400">L. fulvus</span>
                  <span className="text-[10px] text-slate-400">Blacktail snapper</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSampleClick('Canthigaster valentini')}
                  className="px-2.5 py-1.5 rounded-lg bg-marine-950 border border-marine-800 hover:border-ocean-cyan/40 text-left text-slate-300 hover:text-white transition-colors"
                >
                  <span className="block font-semibold text-[11px] text-teal-400">C. valentini</span>
                  <span className="text-[10px] text-slate-400">Sharpnose puffer</span>
                </button>
              </div>
            </div>

            {/* Inference Parameters & Action Button */}
            <div className="space-y-3 pt-2 border-t border-marine-850">
              <div className="flex items-center justify-between text-xs">
                <label className="text-slate-400 font-sans flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-ocean-cyan" />
                  Top Candidates (k):
                </label>
                <div className="flex gap-1.5">
                  {[3, 5, 10].map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setTopK(k)}
                      className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                        topK === k
                          ? 'bg-ocean-cyan text-marine-950 font-bold'
                          : 'bg-marine-900 text-slate-400 hover:text-white border border-marine-800'
                      }`}
                    >
                      {k}
                    </button>
                  ))}
                </div>
              </div>

              <Button
                variant="primary"
                className="w-full"
                disabled={!selectedFile || isClassifying}
                isLoading={isClassifying}
                leftIcon={<Sparkles className="w-4 h-4" />}
                onClick={handleClassify}
              >
                {isClassifying ? 'Analyzing Image...' : 'Identify Marine Species'}
              </Button>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Prediction Results & Taxonomy (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {!result ? (
            <Card className="p-8 border-marine-800 flex flex-col items-center justify-center text-center h-full min-h-[350px] space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-marine-900 border border-marine-800 flex items-center justify-center text-slate-500">
                <Fish className="w-7 h-7" />
              </div>
              <div className="max-w-md space-y-1">
                <h4 className="text-sm font-bold text-slate-300">
                  Awaiting Image Input
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Upload an underwater fish photograph or select one of the quick test samples on the left to run ResNet-18 taxonomy prediction.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-marine-950 border border-marine-850 text-[11px] text-slate-400 max-w-sm font-mono space-y-1 text-left">
                <div className="text-ocean-cyan font-semibold font-sans">Supported Classification Scope:</div>
                <div>• Damselfishes & Anemonefishes (Pomacentridae)</div>
                <div>• Butterflyfishes (Chaetodontidae)</div>
                <div>• Surgeonfishes (Acanthuridae)</div>
                <div>• Snappers, Wrasses & Soldierfishes</div>
              </div>
            </Card>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Primary Top-1 Prediction Card */}
              <Card className="p-6 border-ocean-cyan/40 bg-gradient-to-br from-marine-900 via-marine-950 to-marine-900 space-y-5 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-ocean-cyan/5 rounded-full blur-2xl pointer-events-none" />

                {/* Top Row: Common Name & Confidence Tier Badge */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono text-ocean-cyan uppercase tracking-wider block">
                      Primary Taxonomic Match (Top-1)
                    </span>
                    <h3 className="text-xl font-extrabold text-white mt-0.5">
                      {result.commonName}
                    </h3>
                    <p className="text-sm italic font-serif text-ocean-cyan/90 font-medium">
                      {result.species}
                    </p>
                  </div>
                  <div className="flex flex-col sm:items-end gap-1">
                    {getTierBadge(result.confidenceTier)}
                    <span className="text-2xl font-black font-mono text-white">
                      {(result.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Biological Context Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-xl bg-marine-950/80 border border-marine-800 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-400 block font-sans">Family:</span>
                    <span className="text-white font-semibold">{result.family}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block font-sans">IUCN Red List:</span>
                    <span className={result.iucnStatus === 'Near Threatened' ? 'text-ocean-amber font-semibold' : 'text-ocean-teal font-semibold'}>
                      {result.iucnStatus || 'Least Concern'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block font-sans">WoRMS ID:</span>
                    {result.wormsAphiaId ? (
                      <a
                        href={`https://www.marinespecies.org/aphia.php?p=taxdetails&id=${result.wormsAphiaId}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-ocean-cyan hover:underline inline-flex items-center gap-1"
                      >
                        {result.wormsAphiaId}
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block font-sans">Latency:</span>
                    <span className="text-slate-300">{result.inferenceTimeMs.toFixed(1)} ms</span>
                  </div>
                </div>

                {/* Ecological Habitat Description */}
                {result.habitat && (
                  <div className="text-xs text-slate-300 leading-relaxed p-3 rounded-lg bg-marine-900/60 border border-marine-850">
                    <span className="text-ocean-cyan font-semibold">Ecological Niche: </span>
                    {result.habitat}
                  </div>
                )}
              </Card>

              {/* Top-K Candidates Probability Distribution */}
              <Card className="p-5 border-marine-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-4 h-4 text-ocean-cyan" />
                    Top-{result.topPredictions.length} Probability Distribution
                  </h4>
                  <span className="text-[11px] font-mono text-slate-400">
                    Softmax Normalized
                  </span>
                </div>

                <div className="space-y-3">
                  {result.topPredictions.map((cand, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-marine-900 border border-marine-750 flex items-center justify-center font-mono text-[10px] text-slate-400">
                            #{idx + 1}
                          </span>
                          <span className="font-semibold text-white">
                            {cand.commonName}
                          </span>
                          <span className="italic text-slate-400 font-serif text-[11px] hidden sm:inline">
                            ({cand.species})
                          </span>
                        </div>
                        <span className="font-mono font-bold text-ocean-cyan">
                          {(cand.confidence * 100).toFixed(1)}%
                        </span>
                      </div>

                      {/* Probability Progress Bar */}
                      <div className="w-full bg-marine-950 rounded-full h-2 overflow-hidden border border-marine-800">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            idx === 0 
                              ? 'bg-gradient-to-r from-ocean-cyan to-blue-500' 
                              : 'bg-slate-600'
                          }`}
                          style={{ width: `${Math.max(cand.confidence * 100, 2)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Model Execution Metadata Pill */}
                <div className="pt-3 border-t border-marine-850 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400 gap-2">
                  <span>Architecture: {result.modelArchitecture}</span>
                  <span>Model: v{result.modelVersion}</span>
                  <span>Hardware: {result.device.toUpperCase()}</span>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* 10 Supported Marine Species Modal */}
      <Modal
        isOpen={isCatalogModalOpen}
        onClose={() => setIsCatalogModalOpen(false)}
        title="ResNet-18 Supported Marine Species Catalog (10 Target Taxa)"
        maxWidth="2xl"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            The Phase 14.2 computer vision model is specialized for high-accuracy identification of these 10 reef & pelagic marine species:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-1">
            {modelInfo?.supportedSpecies.map((sp) => (
              <div
                key={sp.classId}
                className="p-3.5 rounded-xl bg-marine-950 border border-marine-800 space-y-1.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h5 className="text-xs font-bold text-white">{sp.commonName}</h5>
                    <p className="text-[11px] italic font-serif text-ocean-cyan">{sp.scientificName}</p>
                  </div>
                  <span className="px-1.5 py-0.5 rounded bg-marine-900 border border-marine-700 text-[10px] font-mono text-slate-400">
                    ID #{sp.classId}
                  </span>
                </div>

                <div className="text-[11px] font-mono text-slate-400 space-y-0.5">
                  <div><span className="text-slate-500 font-sans">Family: </span>{sp.family}</div>
                  <div><span className="text-slate-500 font-sans">Trophic: </span>{sp.trophicGuild}</div>
                  {sp.depthRangeM && (
                    <div><span className="text-slate-500 font-sans">Depth: </span>{sp.depthRangeM[0]}–{sp.depthRangeM[1]} m</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  );
};
