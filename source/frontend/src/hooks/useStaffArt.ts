import { useEffect, useState } from "react";
import { staffDirectoryApi } from "../api/staffDirectoryApi";
import { staffArt, type StaffArt } from "../utils/staffArt";

/** The same picture the front page shows for this person (matched by name in the public staff list). */
export function useStaffArt(fullName: string | undefined): StaffArt | null {
  const [art, setArt] = useState<StaffArt | null>(null);
  useEffect(() => {
    if (!fullName) return;
    let cancelled = false;
    staffDirectoryApi
      .list()
      .then((list) => {
        const index = list.findIndex((m) => m.full_name === fullName);
        if (!cancelled) setArt(staffArt(fullName, index >= 0 ? index : 0));
      })
      .catch(() => {
        if (!cancelled) setArt(staffArt(fullName, 0));
      });
    return () => {
      cancelled = true;
    };
  }, [fullName]);
  return art ?? (fullName ? staffArt(fullName, 0) : null);
}