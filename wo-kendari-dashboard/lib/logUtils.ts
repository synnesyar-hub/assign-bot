// lib/logUtils.ts
import { supabase } from '@/lib/supabase'

export function normalizeDescriptionHtml(html: string): string {
  const stripped = html.replace(/<[^>]*>/g, '').trim()
  return stripped ? html : ''
}

export async function submitLogUpdate(
  table: string,
  incident: string,
  summary: string,
  descriptionHtml: string,
  photoFile: File | null
): Promise<void> {
  let photoPath: string | null = null

  if (photoFile) {
    const ext = photoFile.name.split('.').pop() || 'jpg'
    photoPath = `${incident}-${Date.now()}.${ext}`
    const { error: uploadError } = await supabase.storage
      .from('worklog-temp')
      .upload(photoPath, photoFile, { upsert: true })
    if (uploadError) throw uploadError
  }

  const { error } = await supabase
    .from(table)
    .update({
      log: normalizeDescriptionHtml(descriptionHtml),
      log_summary: summary,
      log_photo_path: photoPath,
      log_synced: false,
      log_sync_error: null,
    })
    .eq('incident', incident)

  if (error) throw error
}