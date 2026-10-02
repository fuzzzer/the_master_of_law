"""Case chat (case_intake) end to end: interview -> case file -> claim document."""
import asyncio, json, sys
import httpx
from harness import BASE, OUT, headers, dialogue, summarize

INTERVIEW = [
    "მინდა საქმე გავხსნა. დამსაქმებელმა უკანონოდ გამათავისუფლა.",
    "შპს 'ალფა ტრეიდი', თბილისი. ვმუშაობდი ბუღალტრად 2023 წლის მარტიდან, უვადო წერილობითი ხელშეკრულებით, ხელფასი 1800 ლარი ხელზე.",
    "2026 წლის 15 სექტემბერს დირექტორმა გიორგი ბერიძემ სიტყვიერად მითხრა აღარ მოხვიდეო. ბრძანება არ გადმოუციათ. მიზეზი არ უთქვამთ, ვფიქრობ იმიტომ რომ ორსულად ვარ და ვუთხარი წინა კვირას.",
    "ივლისის და აგვისტოს ხელფასი არ ჩაურიცხავთ. მაქვს ხელშეკრულების ასლი, საბანკო ამონაწერი, და whatsapp მიმოწერა დირექტორთან სადაც წერს 'აღარ გვჭირდები'. მოწმე - კოლეგა ნინო.",
    "მინდა სამსახურში აღდგენა, იძულებითი განაცდურის ანაზღაურება და ორი თვის ხელფასი. წერილობით ჯერ არაფერი მომითხოვია მათგან.",
    "კი, ეს ყველაფერია. გთხოვ მოამზადე საქმე.",
]


async def main():
    rec = await dialogue("case_intake_labor", INTERVIEW, mode="case_intake")
    summarize(rec)
    dev, conv = rec["device"], rec["conversation_id"]
    async with httpx.AsyncClient(timeout=300) as c:
        h = headers(dev)
        files = (await c.get(f"{BASE}/api/v1/case-files", headers=h)).json()
        print("\n=== case files:", json.dumps(files, ensure_ascii=False)[:1500])
        items = files if isinstance(files, list) else files.get("case_files") or files.get("items") or []
        if not items:
            r = await c.post(f"{BASE}/api/v1/case-files/build", json={"conversation_id": conv}, headers=h)
            print("=== manual build", r.status_code, r.text[:3000])
            items = [r.json()] if r.status_code < 300 else []
        if items:
            cid = items[0].get("id") or items[0].get("case_file_id")
            full = (await c.get(f"{BASE}/api/v1/case-files/{cid}", headers=h)).json()
            (OUT / "case_file.json").write_text(json.dumps(full, ensure_ascii=False, indent=1))
            print("=== case file detail:", json.dumps(full, ensure_ascii=False)[:5000])
            await asyncio.sleep(30)
            d = await c.post(f"{BASE}/api/v1/case-files/{cid}/generate-document",
                             json={"document_type": "სარჩელი"}, headers=h)
            (OUT / "document.json").write_text(d.text)
            print("=== document", d.status_code, d.text[:6000])

asyncio.run(main())
