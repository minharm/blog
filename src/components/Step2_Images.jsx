import { useProjectStore } from '../store/useProjectStore';

export default function Step2_Images() {
  const { projectData, selectedImages, handleToggleImage, handleLocalImageUpload, moveSelected, setCurrentStep, fxSettings, toggleFxSetting } = useProjectStore();

  return (
    <div className="animate-fade-in">
      <button onClick={() => setCurrentStep(1)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 font-bold mb-4 transition-colors">← 이전</button>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">STEP 2</span>
      </div>
      <h3 className="text-2xl font-black text-slate-900">영상에 넣을 이미지를 골라 주세요</h3>
      <p className="text-slate-500 text-sm mt-1.5 mb-5">고른 이미지는 아래 순서대로 영상에 들어가요. 직접 올린 사진도 함께 쓸 수 있어요.</p>

      {/* AI 화질 보정 토글 */}
      <div className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3 mb-5 shadow-sm">
        <div>
          <span className="text-sm font-bold text-slate-800 block">AI 화질 보정</span>
          <span className="text-xs text-slate-400">저화질 이미지를 또렷하게 보정해 영상에 넣어요.</span>
        </div>
        <button onClick={() => toggleFxSetting('upscale')}
          className={`w-11 h-6 rounded-full transition-colors relative ${fxSettings.upscale ? 'bg-indigo-600' : 'bg-slate-300'}`} aria-pressed={fxSettings.upscale}>
          <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${fxSettings.upscale ? 'translate-x-5' : ''}`} />
        </button>
      </div>

      {/* 이미지 고르기 그리드 */}
      <p className="text-xs font-bold text-slate-400 mb-2">이미지 고르기</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3.5 mb-7">
        <label className="group relative aspect-[3/4] bg-white border-2 border-dashed border-gray-300 hover:border-indigo-400 rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all gap-1.5">
          <span className="text-2xl text-slate-300 group-hover:text-indigo-400 transition-colors">＋</span>
          <span className="text-xs font-bold text-slate-400 group-hover:text-indigo-500">사진 올리기</span>
          <input type="file" accept="image/*" multiple className="hidden" onChange={handleLocalImageUpload} />
        </label>

        {projectData.images.map((imgUrl, index) => {
          const order = selectedImages.indexOf(imgUrl);
          const isChecked = order !== -1;
          return (
            <button key={index} onClick={() => handleToggleImage(imgUrl)}
              className={`group relative aspect-[3/4] bg-slate-100 rounded-2xl overflow-hidden cursor-pointer border-2 transition-all ${isChecked ? 'border-indigo-500' : 'border-transparent hover:border-gray-300'}`}>
              <img src={imgUrl} alt={`이미지 ${index + 1}`} loading="lazy" referrerPolicy="no-referrer" className="w-full h-full object-cover" />
              {isChecked && <div className="absolute inset-0 bg-indigo-600/10" />}
              <span className={`absolute top-2 left-2 min-w-6 h-6 px-1.5 rounded-full flex items-center justify-center text-xs font-bold transition-all ${isChecked ? 'bg-indigo-600 text-white' : 'bg-white/80 text-transparent border border-white'}`}>
                {isChecked ? order + 1 : '✓'}
              </span>
            </button>
          );
        })}
      </div>

      {/* 선택한 순서 — 좌우 버튼으로 재배치 */}
      {selectedImages.length > 0 && (
        <div className="mb-8">
          <p className="text-xs font-bold text-slate-400 mb-2">나오는 순서 ({selectedImages.length}장) · 화살표로 바꿔요</p>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {selectedImages.map((imgUrl, i) => (
              <div key={imgUrl} className="shrink-0 w-24">
                <div className="relative aspect-[3/4] rounded-xl overflow-hidden border border-gray-200 bg-slate-100">
                  <img src={imgUrl} alt={`순서 ${i + 1}`} referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                  <span className="absolute top-1.5 left-1.5 w-5 h-5 rounded-full bg-indigo-600 text-white text-[11px] font-bold flex items-center justify-center">{i + 1}</span>
                </div>
                <div className="flex gap-1 mt-1.5">
                  <button onClick={() => moveSelected(i, -1)} disabled={i === 0}
                    className="flex-1 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold disabled:opacity-30 disabled:cursor-not-allowed transition-colors" aria-label="앞으로">◀</button>
                  <button onClick={() => moveSelected(i, 1)} disabled={i === selectedImages.length - 1}
                    className="flex-1 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold disabled:opacity-30 disabled:cursor-not-allowed transition-colors" aria-label="뒤로">▶</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400"><strong className="text-slate-700">{selectedImages.length}장</strong> 선택됨</span>
        <button onClick={() => setCurrentStep(3)} className="px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition-all">목소리 선택 →</button>
      </div>
    </div>
  );
}
