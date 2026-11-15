import { Typography } from 'antd'
import { BLACKOUT_SEASON } from '@/utils/blackout'

const { Text, Link } = Typography

export default function BlackoutSeasonNotice({ style }) {
  return (
    <Text type="secondary" style={{ fontSize: 11, ...style }}>
      {BLACKOUT_SEASON.notice} check{' '}
      <Link href={BLACKOUT_SEASON.link.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 11 }}>
        {BLACKOUT_SEASON.link.text}
      </Link>{' '}
      before you go.
    </Text>
  )
}
