import { useProjectStore } from '../store/useProjectStore';

export default function Step2_Images() {
  const { projectData, selectedImages, handleToggleImage, handleLocalImageUpload, setCurrentStep } = useProjectStore();

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <button onClick={() => setCurrentStep(1)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
        <span className="text-xs font-bold text-blue-400 uppercase">Step 2</span>
      </div>
      <h3 className="text-2xl font-black text-white mb-2">주요 이미지를 선택해주세요</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <label className="group relative aspect-video bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all gap-1.5 order-first">
          <span className="text-xl">➕</span>
          <span className="text-xs font-bold text-slate-500 group-hover:text-blue-400">이미지 추가</span>
          <input type="file" accept="image/*" multiple className="hidden" onChange={handleLocalImageUpload} />
        </label>
        {projectData.images.map((imgUrl, index) => {
          const isChecked = selectedImages.includes(imgUrl);
          return (
            <div key={index} onClick={() => handleToggleImage(imgUrl)} className={`group relative aspect-video bg-slate-900 rounded-xl overflow-hidden cursor-pointer border-2 ${isChecked ? 'border-blue-500 scale-[0.99]' : 'border-slate-800'}`}>
              <div className={`absolute top-2 left-2 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${isChecked ? 'bg-blue-600 text-white' : 'bg-black/50 border border-white/30 text-transparent'}`}>✓</div>
              <img src={imgUrl} alt="asset" className="w-full h-full object-cover" referrerPolicy="no-referrer" />
            </div>
          );
        })}
      </div>
      <button onClick={() => setCurrentStep(3)} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">선택 완료 및 목소리 지정 ➔</button>
    </div>
  );
}